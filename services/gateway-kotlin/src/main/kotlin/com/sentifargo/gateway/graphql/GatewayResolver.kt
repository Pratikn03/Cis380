package com.sentifargo.gateway.graphql

import com.sentifargo.gateway.model.AuthPayload
import com.sentifargo.gateway.model.DashboardSummary
import com.sentifargo.gateway.model.DatasetRecord
import com.sentifargo.gateway.model.FinalizeUploadInput
import com.sentifargo.gateway.model.FinalizeUploadResult
import com.sentifargo.gateway.model.InferenceTraceEvent
import com.sentifargo.gateway.model.JobProgressEvent
import com.sentifargo.gateway.model.JobRecord
import com.sentifargo.gateway.model.MediaAnalyzeInput
import com.sentifargo.gateway.model.ModelRecord
import com.sentifargo.gateway.model.RagAnswer
import com.sentifargo.gateway.model.RagStatus
import com.sentifargo.gateway.model.RecommendationResult
import com.sentifargo.gateway.model.RiskInput
import com.sentifargo.gateway.model.RiskResult
import com.sentifargo.gateway.model.ScoreResult
import com.sentifargo.gateway.model.StartJobInput
import com.sentifargo.gateway.model.SystemAlert
import com.sentifargo.gateway.model.SystemHealth
import com.sentifargo.gateway.model.TrainingDomain
import com.sentifargo.gateway.model.TrainingOverview
import com.sentifargo.gateway.model.UploadSessionInput
import com.sentifargo.gateway.model.UploadSessionResult
import com.sentifargo.gateway.model.Viewer
import com.sentifargo.gateway.service.EventStreamService
import com.sentifargo.gateway.service.FastApiClient
import com.sentifargo.gateway.service.UploadService
import graphql.GraphqlErrorException
import java.time.Duration
import java.util.UUID
import org.springframework.graphql.data.method.annotation.Argument
import org.springframework.graphql.data.method.annotation.ContextValue
import org.springframework.graphql.data.method.annotation.MutationMapping
import org.springframework.graphql.data.method.annotation.QueryMapping
import org.springframework.graphql.data.method.annotation.SubscriptionMapping
import org.springframework.graphql.execution.ErrorType
import org.springframework.stereotype.Controller
import reactor.core.publisher.Flux
import reactor.core.publisher.Mono

@Controller
class GatewayResolver(
    private val fastApiClient: FastApiClient,
    private val eventStreamService: EventStreamService,
    private val uploadService: UploadService,
) {
    private fun requireAuthHeader(authToken: String?): String {
        val raw = authToken?.trim()
        if (raw.isNullOrBlank()) {
            throw GraphqlErrorException.newErrorException()
                .message("Missing authorization token")
                .errorClassification(ErrorType.UNAUTHORIZED)
                .build()
        }
        return if (raw.startsWith("Bearer ", ignoreCase = true)) raw else "Bearer $raw"
    }

    private fun badRequest(message: String): GraphqlErrorException {
        return GraphqlErrorException.newErrorException()
            .message(message)
            .errorClassification(ErrorType.BAD_REQUEST)
            .build()
    }

    @QueryMapping
    fun viewer(@ContextValue("authToken") authToken: String?): Mono<Viewer?> {
        val authHeader = requireAuthHeader(authToken)
        return fastApiClient.viewer(authHeader)
    }

    @QueryMapping
    fun systemHealth(@ContextValue("authToken") authToken: String?): Mono<SystemHealth> {
        val authHeader = requireAuthHeader(authToken)
        return fastApiClient.systemHealth(authHeader)
    }

    @QueryMapping
    fun jobs(
        @Argument limit: Int?,
        @ContextValue("authToken") authToken: String?,
    ): Mono<List<JobRecord>> {
        val authHeader = requireAuthHeader(authToken)
        return fastApiClient.jobs(limit ?: 50, authHeader)
    }

    @QueryMapping
    fun job(@Argument id: String, @ContextValue("authToken") authToken: String?): Mono<JobRecord?> {
        val authHeader = requireAuthHeader(authToken)
        return fastApiClient.job(id, authHeader)
    }

    @QueryMapping
    fun models(@ContextValue("authToken") authToken: String?): Mono<List<ModelRecord>> {
        val authHeader = requireAuthHeader(authToken)
        return fastApiClient.models(authHeader)
    }

    @QueryMapping
    fun datasets(@ContextValue("authToken") authToken: String?): Mono<List<DatasetRecord>> {
        val authHeader = requireAuthHeader(authToken)
        return fastApiClient.datasets(authHeader)
    }

    @QueryMapping
    fun ragStatus(@ContextValue("authToken") authToken: String?): Mono<RagStatus> {
        val authHeader = requireAuthHeader(authToken)
        return fastApiClient.ragStatus(authHeader)
    }

    @QueryMapping
    fun dashboardSummary(@ContextValue("authToken") authToken: String?): Mono<DashboardSummary> {
        val authHeader = requireAuthHeader(authToken)
        return fastApiClient.dashboardSummary(authHeader)
    }

    @QueryMapping
    fun trainingOverview(@ContextValue("authToken") authToken: String?): Mono<TrainingOverview> {
        val authHeader = requireAuthHeader(authToken)
        return fastApiClient.trainingOverview(authHeader)
    }

    @QueryMapping
    fun trainingDomain(
        @Argument domain: String,
        @ContextValue("authToken") authToken: String?,
    ): Mono<TrainingDomain> {
        val authHeader = requireAuthHeader(authToken)
        return fastApiClient.trainingDomain(domain, authHeader)
    }

    @MutationMapping
    fun login(@Argument username: String, @Argument password: String): Mono<AuthPayload> {
        return fastApiClient.login(username, password)
    }

    @MutationMapping
    fun refreshToken(@Argument token: String): Mono<AuthPayload> {
        return fastApiClient.refresh(token)
    }

    @MutationMapping
    fun startJob(
        @Argument input: StartJobInput,
        @ContextValue("authToken") authToken: String?,
    ): Mono<JobRecord> {
        val authHeader = requireAuthHeader(authToken)
        return fastApiClient.startJob(input, authHeader)
            .doOnNext {
                eventStreamService.publishJobProgress(it.jobId, "queued", 0.0, "queued")
                eventStreamService.publishInferenceTrace(
                    correlationId = it.jobId,
                    step = "job.dispatch",
                    status = "started",
                    message = "Job dispatched to worker queue",
                )
            }
    }

    @MutationMapping
    fun queryRag(
        @Argument query: String,
        @Argument topK: Int?,
        @Argument returnChunks: Boolean?,
        @ContextValue("authToken") authToken: String?,
    ): Mono<RagAnswer> {
        val authHeader = requireAuthHeader(authToken)
        val correlationId = UUID.randomUUID().toString()
        eventStreamService.publishInferenceTrace(correlationId, "rag.parse", "started", "Parsing query")

        return fastApiClient.queryRag(query, topK ?: 6, returnChunks ?: false, authHeader)
            .doOnNext {
                eventStreamService.publishInferenceTrace(correlationId, "rag.retrieve", "success", "Retrieved chunks")
            }
    }

    @MutationMapping
    fun runRisk(
        @Argument input: RiskInput,
        @ContextValue("authToken") authToken: String?,
    ): Mono<RiskResult> {
        val authHeader = requireAuthHeader(authToken)
        val correlationId = UUID.randomUUID().toString()
        eventStreamService.publishInferenceTrace(correlationId, "risk.features", "started", "Building risk features")

        return fastApiClient.runRisk(input, authHeader)
            .doOnNext {
                eventStreamService.publishInferenceTrace(
                    correlationId,
                    "risk.fusion",
                    "success",
                    "Fusion decision: ${it.decision}",
                )
            }
    }

    @MutationMapping
    fun scoreFraud(
        @Argument features: List<Double>,
        @ContextValue("authToken") authToken: String?,
    ): Mono<ScoreResult> {
        val authHeader = requireAuthHeader(authToken)
        return fastApiClient.scoreFraud(features, authHeader)
    }

    @MutationMapping
    fun scoreCyber(
        @Argument features: List<Double>,
        @ContextValue("authToken") authToken: String?,
    ): Mono<ScoreResult> {
        val authHeader = requireAuthHeader(authToken)
        return fastApiClient.scoreCyber(features, authHeader)
    }

    @MutationMapping
    fun scoreBehavior(
        @Argument features: List<Double>,
        @ContextValue("authToken") authToken: String?,
    ): Mono<ScoreResult> {
        val authHeader = requireAuthHeader(authToken)
        return fastApiClient.scoreBehavior(features, authHeader)
    }

    @MutationMapping
    fun createUploadSession(
        @Argument input: UploadSessionInput,
        @ContextValue("authToken") authToken: String?,
    ): UploadSessionResult {
        val authHeader = requireAuthHeader(authToken)
        return try {
            uploadService.createUploadSession(input, authHeader)
        } catch (ex: IllegalArgumentException) {
            throw badRequest(ex.message ?: "Invalid upload session request.")
        }
    }

    @MutationMapping
    fun finalizeUpload(
        @Argument input: FinalizeUploadInput,
        @ContextValue("authToken") authToken: String?,
    ): FinalizeUploadResult {
        val authHeader = requireAuthHeader(authToken)
        val result = try {
            uploadService.finalizeUpload(input, authHeader)
        } catch (ex: IllegalArgumentException) {
            throw badRequest(ex.message ?: "Invalid finalize upload request.")
        }
        eventStreamService.publishInferenceTrace(
            correlationId = input.correlationId,
            step = "upload.finalize",
            status = "accepted",
            message = "Upload accepted for ${input.tool} processing",
        )
        return result
    }

    @MutationMapping
    fun missionChat(
        @Argument prompt: String,
        @Argument useRag: Boolean?,
        @ContextValue("authToken") authToken: String?,
    ): Mono<Map<String, Any?>> {
        val authHeader = requireAuthHeader(authToken)
        return fastApiClient.missionChat(prompt, useRag ?: true, authHeader)
    }

    @MutationMapping
    fun recommendMovies(
        @Argument prompt: String,
        @Argument topK: Int?,
        @ContextValue("authToken") authToken: String?,
    ): Mono<RecommendationResult> {
        val authHeader = requireAuthHeader(authToken)
        return fastApiClient.recommendMovies(prompt, topK ?: 5, authHeader)
    }

    @MutationMapping
    fun recommendClothes(
        @Argument prompt: String,
        @Argument topK: Int?,
        @ContextValue("authToken") authToken: String?,
    ): Mono<RecommendationResult> {
        val authHeader = requireAuthHeader(authToken)
        return fastApiClient.recommendClothes(prompt, topK ?: 5, authHeader)
    }

    @MutationMapping
    fun analyzeVoiceEmotion(
        @Argument input: MediaAnalyzeInput,
        @ContextValue("authToken") authToken: String?,
    ): Mono<Map<String, Any?>> {
        val authHeader = requireAuthHeader(authToken)
        return fastApiClient.analyzeVoiceEmotion(input, authHeader)
    }

    @MutationMapping
    fun analyzeVideoEmotion(
        @Argument input: MediaAnalyzeInput,
        @ContextValue("authToken") authToken: String?,
    ): Mono<Map<String, Any?>> {
        val authHeader = requireAuthHeader(authToken)
        return fastApiClient.analyzeVideoEmotion(input, authHeader)
    }

    @MutationMapping
    fun detectDeepfake(
        @Argument input: MediaAnalyzeInput,
        @ContextValue("authToken") authToken: String?,
    ): Mono<Map<String, Any?>> {
        val authHeader = requireAuthHeader(authToken)
        return fastApiClient.detectDeepfake(input, authHeader)
    }

    @MutationMapping
    fun detectBrandLogos(
        @Argument input: MediaAnalyzeInput,
        @ContextValue("authToken") authToken: String?,
    ): Mono<Map<String, Any?>> {
        val authHeader = requireAuthHeader(authToken)
        return fastApiClient.detectBrandLogos(input, authHeader)
    }

    @SubscriptionMapping
    fun jobProgress(
        @Argument jobId: String,
        @ContextValue("authToken") authToken: String?,
    ): Flux<JobProgressEvent> {
        requireAuthHeader(authToken)
        val pulse = Flux.interval(Duration.ofSeconds(5)).map {
            JobProgressEvent(
                jobId = jobId,
                status = "running",
                progress = (it % 100).toDouble() / 100.0,
                message = "Worker heartbeat",
                timestamp = java.time.Instant.now().toString(),
            )
        }
        return Flux.merge(eventStreamService.jobProgress(jobId), pulse)
    }

    @SubscriptionMapping
    fun inferenceTrace(
        @Argument correlationId: String,
        @ContextValue("authToken") authToken: String?,
    ): Flux<InferenceTraceEvent> {
        requireAuthHeader(authToken)
        return eventStreamService.inferenceTrace(correlationId)
    }

    @SubscriptionMapping
    fun systemAlerts(@ContextValue("authToken") authToken: String?): Flux<SystemAlert> {
        val authHeader = requireAuthHeader(authToken)
        val healthPulse = Flux.interval(Duration.ofSeconds(15))
            .flatMap { fastApiClient.systemHealth(authHeader) }
            .map {
                SystemAlert(
                    level = if (it.status == "ok") "INFO" else "WARN",
                    message = "${it.service} status=${it.status}",
                    component = "gateway",
                    timestamp = java.time.Instant.now().toString(),
                )
            }
        return Flux.merge(eventStreamService.systemAlerts(), healthPulse)
    }
}

package com.sentifargo.gateway.service

import com.fasterxml.jackson.databind.JsonNode
import com.fasterxml.jackson.databind.ObjectMapper
import com.sentifargo.gateway.model.AuthPayload
import com.sentifargo.gateway.model.DashboardAlert
import com.sentifargo.gateway.model.DashboardSummary
import com.sentifargo.gateway.model.DatasetRecord
import com.sentifargo.gateway.model.JobRecord
import com.sentifargo.gateway.model.MediaAnalyzeInput
import com.sentifargo.gateway.model.ModelRecord
import com.sentifargo.gateway.model.RagAnswer
import com.sentifargo.gateway.model.RagStatus
import com.sentifargo.gateway.model.RecommendationItem
import com.sentifargo.gateway.model.RecommendationResult
import com.sentifargo.gateway.model.RiskInput
import com.sentifargo.gateway.model.RiskResult
import com.sentifargo.gateway.model.ScoreResult
import com.sentifargo.gateway.model.StartJobInput
import com.sentifargo.gateway.model.SystemHealth
import com.sentifargo.gateway.model.TrainingDomain
import com.sentifargo.gateway.model.TrainingMetrics
import com.sentifargo.gateway.model.TrainingOverview
import com.sentifargo.gateway.model.Viewer
import org.springframework.http.HttpHeaders
import org.springframework.stereotype.Service
import org.springframework.util.LinkedMultiValueMap
import org.springframework.web.reactive.function.BodyInserters
import org.springframework.web.reactive.function.client.WebClient
import reactor.core.publisher.Mono

@Service
class FastApiClient(
    private val webClient: WebClient,
    private val objectMapper: ObjectMapper,
) {
    private fun authHeaders(authToken: String?): Pair<String, String>? {
        if (authToken.isNullOrBlank()) return null
        return HttpHeaders.AUTHORIZATION to authToken
    }

    private fun textOrNull(node: JsonNode, field: String): String? {
        val fieldNode = node.path(field)
        if (fieldNode.isMissingNode || fieldNode.isNull) return null
        return fieldNode.asText()
    }

    @Suppress("UNCHECKED_CAST")
    private fun jsonToMap(node: JsonNode): Map<String, Any?> {
        return objectMapper.convertValue(node, Map::class.java) as? Map<String, Any?> ?: emptyMap()
    }

    fun login(username: String, password: String): Mono<AuthPayload> {
        return webClient.post().uri("/api/v1/auth/login")
            .bodyValue(mapOf("username" to username, "password" to password))
            .retrieve()
            .bodyToMono(JsonNode::class.java)
            .map { node ->
                AuthPayload(
                    accessToken = node.path("access_token").asText(),
                    refreshToken = node.path("refresh_token").asText(),
                    tokenType = node.path("token_type").asText("bearer"),
                )
            }
    }

    fun refresh(refreshToken: String): Mono<AuthPayload> {
        return webClient.post().uri("/api/v1/auth/refresh")
            .bodyValue(mapOf("refresh_token" to refreshToken))
            .retrieve()
            .bodyToMono(JsonNode::class.java)
            .map { node ->
                AuthPayload(
                    accessToken = node.path("access_token").asText(),
                    refreshToken = node.path("refresh_token").asText(),
                    tokenType = node.path("token_type").asText("bearer"),
                )
            }
    }

    fun viewer(authToken: String?): Mono<Viewer?> {
        val request = webClient.get().uri("/api/v1/users/me")
        authHeaders(authToken)?.let { (k, v) -> request.header(k, v) }
        return request.retrieve().bodyToMono(JsonNode::class.java)
            .map<Viewer?> { node ->
                Viewer(
                    id = node.path("id").asText(),
                    username = node.path("username").asText(),
                    email = textOrNull(node, "email"),
                    roles = node.path("roles").map { it.asText() },
                    isActive = node.path("is_active").asBoolean(true),
                )
            }
            .onErrorResume { Mono.empty() }
    }

    fun systemHealth(authToken: String?): Mono<SystemHealth> {
        val request = webClient.get().uri("/api/health")
        authHeaders(authToken)?.let { (k, v) -> request.header(k, v) }
        return request.retrieve().bodyToMono(JsonNode::class.java)
            .map { node ->
                SystemHealth(
                    status = node.path("status").asText("unknown"),
                    service = node.path("service").asText("sentifargo"),
                    version = node.path("version").asText("unknown"),
                    uptimeSeconds = node.path("uptime_seconds").takeIf { !it.isMissingNode }?.asDouble(),
                )
            }
    }

    fun jobs(limit: Int, authToken: String?): Mono<List<JobRecord>> {
        val request = webClient.get().uri("/api/v1/jobs?limit=$limit")
        authHeaders(authToken)?.let { (k, v) -> request.header(k, v) }
        return request.retrieve().bodyToMono(JsonNode::class.java)
            .map { node -> node.map { mapJob(it) } }
    }

    fun job(id: String, authToken: String?): Mono<JobRecord?> {
        val request = webClient.get().uri("/api/v1/jobs/$id")
        authHeaders(authToken)?.let { (k, v) -> request.header(k, v) }
        return request.retrieve().bodyToMono(JsonNode::class.java)
            .map<JobRecord?> { mapJob(it) }
            .onErrorResume { Mono.empty() }
    }

    fun startJob(input: StartJobInput, authToken: String?): Mono<JobRecord> {
        val payload = mutableMapOf<String, Any>("type" to input.type)
        val inner = mutableMapOf<String, Any>()
        input.rebuild?.let { inner["rebuild"] = it }
        input.script?.let { inner["script"] = it }
        input.args?.let { inner["args"] = it }
        payload["payload"] = inner

        val request = webClient.post().uri("/api/v1/jobs/start")
        authHeaders(authToken)?.let { (k, v) -> request.header(k, v) }
        return request.bodyValue(payload).retrieve().bodyToMono(JsonNode::class.java)
            .map { node ->
                JobRecord(
                    jobId = node.path("job_id").asText(),
                    taskId = textOrNull(node, "task_id"),
                    type = input.type,
                    status = node.path("status").asText("queued"),
                    progress = 0.0,
                    message = "queued",
                    createdAt = null,
                )
            }
    }

    fun models(authToken: String?): Mono<List<ModelRecord>> {
        val request = webClient.get().uri("/api/v1/models")
        authHeaders(authToken)?.let { (k, v) -> request.header(k, v) }
        return request.retrieve().bodyToMono(JsonNode::class.java)
            .map { node ->
                node.map {
                    ModelRecord(
                        id = it.path("id").asText(),
                        modelName = it.path("model_name").asText(),
                        version = it.path("version").asText(),
                        status = it.path("status").asText("unknown"),
                        createdAt = textOrNull(it, "created_at"),
                    )
                }
            }
    }

    fun datasets(authToken: String?): Mono<List<DatasetRecord>> {
        val request = webClient.get().uri("/api/v1/datasets")
        authHeaders(authToken)?.let { (k, v) -> request.header(k, v) }
        return request.retrieve().bodyToMono(JsonNode::class.java)
            .map { node ->
                node.map {
                    DatasetRecord(
                        id = it.path("id").asText(),
                        name = it.path("name").asText(),
                        location = it.path("location").asText(),
                        license = it.path("license").asText("unknown"),
                        sizeBytes = it.path("size_bytes").asLong(0),
                        createdAt = textOrNull(it, "created_at"),
                    )
                }
            }
    }

    fun ragStatus(authToken: String?): Mono<RagStatus> {
        val request = webClient.get().uri("/api/rag/status")
        authHeaders(authToken)?.let { (k, v) -> request.header(k, v) }
        return request.retrieve().bodyToMono(JsonNode::class.java)
            .map {
                RagStatus(
                    status = it.path("status").asText("unknown"),
                    docsCount = it.path("docs_count").takeIf { v -> !v.isMissingNode }?.asInt(),
                    chunksCount = it.path("chunks_count").takeIf { v -> !v.isMissingNode }?.asInt(),
                )
            }
            .onErrorReturn(RagStatus(status = "unknown", docsCount = null, chunksCount = null))
    }

    fun queryRag(query: String, topK: Int, returnChunks: Boolean, authToken: String?): Mono<RagAnswer> {
        val request = webClient.post().uri("/api/v1/rag/query")
        authHeaders(authToken)?.let { (k, v) -> request.header(k, v) }
        return request.bodyValue(mapOf("query" to query, "top_k" to topK, "return_chunks" to returnChunks))
            .retrieve()
            .bodyToMono(JsonNode::class.java)
            .map { node ->
                RagAnswer(
                    status = node.path("status").asText("ok"),
                    answer = node.path("answer").asText(""),
                    citations = node.path("citations").map { it.asText() },
                    retrieval = if (node.has("retrieval")) objectMapper.writeValueAsString(node.path("retrieval")) else null,
                )
            }
    }

    fun runRisk(input: RiskInput, authToken: String?): Mono<RiskResult> {
        val request = webClient.post().uri("/api/risk/analyze")
        authHeaders(authToken)?.let { (k, v) -> request.header(k, v) }
        return request.bodyValue(
            mapOf(
                "login_country" to input.loginCountry,
                "device_known" to input.deviceKnown,
                "login_time" to input.loginTime,
                "clicks_per_minute" to input.clicksPerMinute,
                "files_accessed" to input.filesAccessed,
                "transaction_amount" to input.transactionAmount,
            ),
        ).retrieve().bodyToMono(JsonNode::class.java)
            .map {
                RiskResult(
                    cyberRisk = it.path("cyber_risk").asDouble(0.0),
                    behaviorRisk = it.path("behavior_risk").asDouble(0.0),
                    fraudRisk = it.path("fraud_risk").asDouble(0.0),
                    fusionRisk = it.path("fusion_risk").asDouble(0.0),
                    decision = it.path("decision").asText("unknown"),
                    reasonCode = it.path("reason_code").asText("unknown"),
                    explanation = textOrNull(it, "explanation"),
                )
            }
    }

    fun scoreFraud(features: List<Double>, authToken: String?): Mono<ScoreResult> {
        val request = webClient.post().uri("/api/fraud")
        authHeaders(authToken)?.let { (k, v) -> request.header(k, v) }
        return request.bodyValue(mapOf("features" to features)).retrieve().bodyToMono(JsonNode::class.java)
            .map {
                ScoreResult(
                    score = it.path("score").asDouble(0.0),
                    inputFeatures = it.path("input_features").asInt(features.size),
                    expectedFeatures = it.path("expected_features").takeIf { v -> !v.isMissingNode && !v.isNull }?.asInt(),
                )
            }
    }

    fun scoreCyber(features: List<Double>, authToken: String?): Mono<ScoreResult> {
        val request = webClient.post().uri("/api/cyber")
        authHeaders(authToken)?.let { (k, v) -> request.header(k, v) }
        return request.bodyValue(mapOf("features" to features)).retrieve().bodyToMono(JsonNode::class.java)
            .map {
                ScoreResult(
                    score = it.path("score").asDouble(0.0),
                    inputFeatures = it.path("input_features").asInt(features.size),
                    expectedFeatures = it.path("expected_features").takeIf { v -> !v.isMissingNode && !v.isNull }?.asInt(),
                )
            }
    }

    fun scoreBehavior(features: List<Double>, authToken: String?): Mono<ScoreResult> {
        val request = webClient.post().uri("/api/behavior")
        authHeaders(authToken)?.let { (k, v) -> request.header(k, v) }
        return request.bodyValue(mapOf("features" to features)).retrieve().bodyToMono(JsonNode::class.java)
            .map {
                ScoreResult(
                    score = it.path("score").asDouble(0.0),
                    inputFeatures = it.path("input_features").asInt(features.size),
                    expectedFeatures = it.path("expected_features").takeIf { v -> !v.isMissingNode && !v.isNull }?.asInt(),
                )
            }
    }

    fun dashboardSummary(authToken: String?): Mono<DashboardSummary> {
        return Mono.zip(systemHealth(authToken), jobs(25, authToken), ragStatus(authToken))
            .map { tuple ->
                val health = tuple.t1
                val jobs = tuple.t2
                val rag = tuple.t3

                val activeJobs = jobs.count { j ->
                    val status = j.status.lowercase()
                    status == "running" || status == "queued" || status == "pending"
                }
                val failedJobs = jobs.count { j ->
                    val status = j.status.lowercase()
                    status.contains("fail") || status.contains("error") || status.contains("blocked")
                }

                val score = ((activeJobs * 4) + (rag.docsCount ?: 0) % 40 + if (health.status == "ok") 35 else 18)
                    .coerceIn(1, 99)

                DashboardSummary(
                    fraudAlerts = failedJobs.coerceAtLeast(0),
                    docsIndexed = (rag.chunksCount ?: 0).coerceAtLeast(0),
                    activeJobs = activeJobs,
                    riskScore = score,
                    alerts = listOf(
                        DashboardAlert(
                            level = if (health.status == "ok") "info" else "warning",
                            message = "${health.service} status=${health.status}",
                            component = "gateway",
                            timestamp = java.time.Instant.now().toString(),
                        ),
                    ),
                )
            }
    }

    fun trainingOverview(authToken: String?): Mono<TrainingOverview> {
        val request = webClient.get().uri("/api/v1/training/overview")
        authHeaders(authToken)?.let { (k, v) -> request.header(k, v) }
        return request.retrieve().bodyToMono(JsonNode::class.java)
            .map { node -> mapTrainingOverview(node) }
    }

    fun trainingDomain(domain: String, authToken: String?): Mono<TrainingDomain> {
        val request = webClient.get().uri("/api/v1/training/domain/$domain")
        authHeaders(authToken)?.let { (k, v) -> request.header(k, v) }
        return request.retrieve().bodyToMono(JsonNode::class.java)
            .map { node -> mapTrainingDomain(node) }
    }

    fun missionChat(prompt: String, useRag: Boolean, authToken: String?): Mono<Map<String, Any?>> {
        val request = webClient.post().uri("/api/chat")
        authHeaders(authToken)?.let { (k, v) -> request.header(k, v) }
        return request
            .bodyValue(mapOf("message" to prompt, "user_id" to "dashboard", "use_rag" to useRag))
            .retrieve()
            .bodyToMono(JsonNode::class.java)
            .map { jsonToMap(it) }
    }

    fun recommendMovies(prompt: String, topK: Int, authToken: String?): Mono<RecommendationResult> {
        val form = LinkedMultiValueMap<String, String>()
        form.add("text", prompt)
        form.add("top_k", topK.toString())
        form.add("use_objects", "false")
        form.add("use_brand", "false")

        val request = webClient.post().uri("/api/recommend/multimodal")
        authHeaders(authToken)?.let { (k, v) -> request.header(k, v) }

        return request
            .body(BodyInserters.fromMultipartData(form))
            .retrieve()
            .bodyToMono(JsonNode::class.java)
            .map { toRecommendationResult(it, "movies") }
            .onErrorReturn(
                RecommendationResult(
                    mode = "movies",
                    items = listOf(
                        RecommendationItem("mv-1", "Interstellar", 0.82, "fallback"),
                        RecommendationItem("mv-2", "Blade Runner 2049", 0.78, "fallback"),
                    ),
                    raw = mapOf("status" to "fallback"),
                ),
            )
    }

    fun recommendClothes(prompt: String, topK: Int, authToken: String?): Mono<RecommendationResult> {
        val form = LinkedMultiValueMap<String, String>()
        form.add("text", prompt)
        form.add("top_k", topK.toString())

        val request = webClient.post().uri("/api/recommend/clothes")
        authHeaders(authToken)?.let { (k, v) -> request.header(k, v) }

        return request
            .body(BodyInserters.fromMultipartData(form))
            .retrieve()
            .bodyToMono(JsonNode::class.java)
            .map { toRecommendationResult(it, "clothes") }
            .onErrorReturn(
                RecommendationResult(
                    mode = "clothes",
                    items = listOf(
                        RecommendationItem("cl-1", "Streetwear Layered Set", 0.76, "fallback"),
                        RecommendationItem("cl-2", "Minimal Tech Runner", 0.71, "fallback"),
                    ),
                    raw = mapOf("status" to "fallback"),
                ),
            )
    }

    fun analyzeVoiceEmotion(input: MediaAnalyzeInput, authToken: String?): Mono<Map<String, Any?>> {
        return missionChat(
            prompt = "Analyze voice emotion for media='${input.mediaUrl ?: input.fileName ?: "unknown"}'",
            useRag = false,
            authToken = authToken,
        ).map { payload ->
            payload + mapOf("task" to "voice_emotion", "status" to (payload["status"] ?: "ok"))
        }
    }

    fun analyzeVideoEmotion(input: MediaAnalyzeInput, authToken: String?): Mono<Map<String, Any?>> {
        return missionChat(
            prompt = "Analyze video emotion for media='${input.mediaUrl ?: input.fileName ?: "unknown"}'",
            useRag = false,
            authToken = authToken,
        ).map { payload ->
            payload + mapOf("task" to "video_emotion", "status" to (payload["status"] ?: "ok"))
        }
    }

    fun detectDeepfake(input: MediaAnalyzeInput, authToken: String?): Mono<Map<String, Any?>> {
        return missionChat(
            prompt = "Detect deepfake for media='${input.mediaUrl ?: input.fileName ?: "unknown"}'",
            useRag = false,
            authToken = authToken,
        ).map { payload ->
            payload + mapOf("task" to "deepfake", "status" to (payload["status"] ?: "ok"))
        }
    }

    fun detectBrandLogos(input: MediaAnalyzeInput, authToken: String?): Mono<Map<String, Any?>> {
        return missionChat(
            prompt = "Detect brand logos for media='${input.mediaUrl ?: input.fileName ?: "unknown"}'",
            useRag = false,
            authToken = authToken,
        ).map { payload ->
            payload + mapOf("task" to "brand_logo", "status" to (payload["status"] ?: "ok"))
        }
    }

    private fun toRecommendationResult(node: JsonNode, mode: String): RecommendationResult {
        val candidates = when {
            node.path("items").isArray -> node.path("items")
            node.path("results").isArray -> node.path("results")
            else -> objectMapper.createArrayNode()
        }

        val items = candidates.mapIndexed { index, item ->
            RecommendationItem(
                id = item.path("id").asText(item.path("movieId").asText("$mode-$index")),
                title = item.path("title").asText(item.path("name").asText("Item ${index + 1}")),
                score = item.path("score").takeIf { !it.isMissingNode }?.asDouble(
                    item.path("probability").asDouble(0.0),
                ) ?: 0.0,
                reason = textOrNull(item, "reason") ?: textOrNull(item, "mode"),
            )
        }

        return RecommendationResult(
            mode = node.path("mode").asText(mode),
            items = items,
            raw = jsonToMap(node),
        )
    }

    private fun mapTrainingOverview(node: JsonNode): TrainingOverview {
        val domains = node.path("domains").map { mapTrainingDomain(it) }
        return TrainingOverview(
            generatedAt = textOrNull(node, "generatedAt"),
            domains = domains,
            readyCount = node.path("readyCount").asInt(domains.count { it.status == "ready" }),
            totalCount = node.path("totalCount").asInt(domains.size),
        )
    }

    private fun mapTrainingDomain(node: JsonNode): TrainingDomain {
        val metricsNode = node.path("metrics")
        val metrics = if (metricsNode.isMissingNode || metricsNode.isNull) {
            null
        } else {
            TrainingMetrics(
                accuracy = metricsNode.path("accuracy").takeIf { !it.isMissingNode && !it.isNull }?.asDouble(),
                f1 = metricsNode.path("f1").takeIf { !it.isMissingNode && !it.isNull }?.asDouble(),
                auc = metricsNode.path("auc").takeIf { !it.isMissingNode && !it.isNull }?.asDouble(),
                precision = metricsNode.path("precision").takeIf { !it.isMissingNode && !it.isNull }?.asDouble(),
                recall = metricsNode.path("recall").takeIf { !it.isMissingNode && !it.isNull }?.asDouble(),
            )
        }

        return TrainingDomain(
            domain = node.path("domain").asText(),
            status = node.path("status").asText("missing"),
            datasetReady = node.path("datasetReady").asBoolean(false),
            modelReady = node.path("modelReady").asBoolean(false),
            metrics = metrics,
            sourcePath = node.path("sourcePath").asText(""),
            updatedAt = textOrNull(node, "updatedAt"),
            blockers = node.path("blockers").map { it.asText() },
        )
    }

    private fun mapJob(node: JsonNode): JobRecord {
        return JobRecord(
            jobId = node.path("job_id").asText(node.path("id").asText()),
            taskId = textOrNull(node, "task_id"),
            type = node.path("type").asText(node.path("job_type").asText("unknown")),
            status = node.path("status").asText("unknown"),
            progress = node.path("progress").asDouble(0.0),
            message = node.path("message").asText(""),
            createdAt = textOrNull(node, "created_at"),
        )
    }
}

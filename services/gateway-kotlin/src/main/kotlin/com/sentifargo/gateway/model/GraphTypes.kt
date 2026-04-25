package com.sentifargo.gateway.model

data class Viewer(
    val id: String,
    val username: String,
    val email: String?,
    val roles: List<String>,
    val isActive: Boolean,
)

data class SystemHealth(
    val status: String,
    val service: String,
    val version: String,
    val uptimeSeconds: Double?,
)

data class JobRecord(
    val jobId: String,
    val taskId: String?,
    val type: String,
    val status: String,
    val progress: Double,
    val message: String,
    val createdAt: String?,
)

data class ModelRecord(
    val id: String,
    val modelName: String,
    val version: String,
    val status: String,
    val createdAt: String?,
)

data class DatasetRecord(
    val id: String,
    val name: String,
    val location: String,
    val license: String,
    val sizeBytes: Long,
    val createdAt: String?,
)

data class RagStatus(
    val status: String,
    val docsCount: Int?,
    val chunksCount: Int?,
)

data class RagAnswer(
    val status: String,
    val answer: String,
    val citations: List<String>,
    val retrieval: String?,
)

data class RiskResult(
    val cyberRisk: Double,
    val behaviorRisk: Double,
    val fraudRisk: Double,
    val fusionRisk: Double,
    val decision: String,
    val reasonCode: String,
    val explanation: String?,
)

data class ScoreResult(
    val score: Double,
    val inputFeatures: Int,
    val expectedFeatures: Int?,
)

data class AuthPayload(
    val accessToken: String,
    val refreshToken: String,
    val tokenType: String,
)

data class UploadSessionResult(
    val uploadUrl: String,
    val objectKey: String,
    val expiresAt: String,
    val maxBytes: Int,
    val contentTypes: List<String>,
)

data class FinalizeUploadResult(
    val status: String,
    val objectKey: String,
    val correlationId: String,
    val jobId: String?,
)

data class JobProgressEvent(
    val jobId: String,
    val status: String,
    val progress: Double,
    val message: String,
    val timestamp: String,
)

data class InferenceTraceEvent(
    val correlationId: String,
    val step: String,
    val status: String,
    val message: String,
    val timestamp: String,
    val latencyMs: Double?,
)

data class SystemAlert(
    val level: String,
    val message: String,
    val component: String,
    val timestamp: String,
)

data class DashboardAlert(
    val level: String,
    val message: String,
    val component: String,
    val timestamp: String,
)

data class DashboardSummary(
    val fraudAlerts: Int,
    val docsIndexed: Int,
    val activeJobs: Int,
    val riskScore: Int,
    val alerts: List<DashboardAlert>,
)

data class RecommendationItem(
    val id: String,
    val title: String,
    val score: Double,
    val reason: String?,
)

data class RecommendationResult(
    val mode: String,
    val items: List<RecommendationItem>,
    val raw: Map<String, Any?>?,
)

data class TrainingMetrics(
    val accuracy: Double?,
    val f1: Double?,
    val auc: Double?,
    val precision: Double?,
    val recall: Double?,
)

data class TrainingDomain(
    val domain: String,
    val status: String,
    val datasetReady: Boolean,
    val modelReady: Boolean,
    val metrics: TrainingMetrics?,
    val sourcePath: String,
    val updatedAt: String?,
    val blockers: List<String>,
    val qualityStatus: String,
    val thresholds: Any?,
    val metricFailures: List<String>,
    val artifactSha256: String?,
)

data class TrainingOverview(
    val generatedAt: String?,
    val domains: List<TrainingDomain>,
    val readyCount: Int,
    val totalCount: Int,
)

data class StartJobInput(
    val type: String,
    val rebuild: Boolean? = null,
    val script: String? = null,
    val args: List<String>? = null,
)

data class RiskInput(
    val loginCountry: String = "US",
    val deviceKnown: Boolean = true,
    val loginTime: Double = 12.0,
    val clicksPerMinute: Double = 10.0,
    val filesAccessed: Int = 0,
    val transactionAmount: Double = 0.0,
)

data class UploadSessionInput(
    val fileName: String,
    val contentType: String,
    val maxBytes: Int? = null,
)

data class FinalizeUploadInput(
    val objectKey: String,
    val tool: String,
    val correlationId: String,
)

data class MediaAnalyzeInput(
    val fileName: String? = null,
    val mediaUrl: String? = null,
)

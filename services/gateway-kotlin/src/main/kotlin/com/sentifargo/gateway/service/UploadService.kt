package com.sentifargo.gateway.service

import com.sentifargo.gateway.config.GatewayProperties
import com.sentifargo.gateway.model.FinalizeUploadInput
import com.sentifargo.gateway.model.FinalizeUploadResult
import com.sentifargo.gateway.model.UploadSessionInput
import com.sentifargo.gateway.model.UploadSessionResult
import java.time.Instant
import java.time.temporal.ChronoUnit
import java.util.UUID
import org.springframework.stereotype.Service
import software.amazon.awssdk.services.s3.S3Client
import software.amazon.awssdk.services.s3.model.HeadObjectRequest
import software.amazon.awssdk.services.s3.model.PutObjectRequest
import software.amazon.awssdk.services.s3.presigner.S3Presigner
import software.amazon.awssdk.services.s3.presigner.model.PutObjectPresignRequest

@Service
class UploadService(
    private val props: GatewayProperties,
    private val presigner: S3Presigner,
    private val s3Client: S3Client,
) {
    private val allowedTools = setOf("vision", "voice", "video", "brand", "rag")
    private val allowedContentTypePrefixes = listOf("image/", "audio/", "video/")
    private val allowedExactContentTypes = setOf(
        "application/pdf",
        "text/plain",
        "application/json",
        "application/octet-stream",
    )

    fun createUploadSession(input: UploadSessionInput): UploadSessionResult {
        require(input.fileName.isNotBlank()) { "fileName is required." }
        require(isAllowedContentType(input.contentType)) { "Unsupported contentType '${input.contentType}'." }
        val now = Instant.now()
        val expiresAt = now.plus(props.uploads.signedUrlMinutes, ChronoUnit.MINUTES)
        val safeFileName = sanitizeFileName(input.fileName)
        val maxBytes = when {
            input.maxBytes == null -> props.uploads.maxBytes
            input.maxBytes <= 0 -> throw IllegalArgumentException("maxBytes must be greater than zero.")
            else -> input.maxBytes.coerceAtMost(props.uploads.maxBytes)
        }
        val objectKey = "uploads/${now.epochSecond}/${UUID.randomUUID()}-$safeFileName"

        val putObjectRequest = PutObjectRequest.builder()
            .bucket(props.uploads.bucket)
            .key(objectKey)
            .contentType(input.contentType)
            .build()

        val presignRequest = PutObjectPresignRequest.builder()
            .signatureDuration(java.time.Duration.ofMinutes(props.uploads.signedUrlMinutes))
            .putObjectRequest(putObjectRequest)
            .build()

        val presigned = presigner.presignPutObject(presignRequest)

        return UploadSessionResult(
            uploadUrl = presigned.url().toExternalForm(),
            objectKey = objectKey,
            expiresAt = expiresAt.toString(),
            maxBytes = maxBytes,
            contentTypes = listOf(input.contentType),
        )
    }

    fun finalizeUpload(input: FinalizeUploadInput): FinalizeUploadResult {
        val normalizedTool = input.tool.trim().lowercase()
        require(normalizedTool in allowedTools) { "Unsupported tool '${input.tool}'." }
        require(input.objectKey.startsWith("uploads/")) { "objectKey must be inside uploads/ namespace." }
        require(input.correlationId.isNotBlank()) { "correlationId is required." }

        val headRequest = HeadObjectRequest.builder()
            .bucket(props.uploads.bucket)
            .key(input.objectKey)
            .build()
        try {
            s3Client.headObject(headRequest)
        } catch (_: Exception) {
            throw IllegalArgumentException("Uploaded object not found or inaccessible for key '${input.objectKey}'.")
        }

        return FinalizeUploadResult(
            status = "accepted",
            objectKey = input.objectKey,
            correlationId = input.correlationId,
            jobId = UUID.randomUUID().toString(),
        )
    }

    private fun sanitizeFileName(fileName: String): String {
        val base = fileName.substringAfterLast('/').substringAfterLast('\\')
        val cleaned = base.replace(Regex("[^A-Za-z0-9._-]"), "_").take(120)
        require(cleaned.isNotBlank()) { "fileName is invalid." }
        return cleaned
    }

    private fun isAllowedContentType(contentType: String): Boolean {
        val normalized = contentType.trim().lowercase()
        return normalized in allowedExactContentTypes || allowedContentTypePrefixes.any { normalized.startsWith(it) }
    }
}

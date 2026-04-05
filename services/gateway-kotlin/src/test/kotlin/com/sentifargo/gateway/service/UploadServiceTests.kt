package com.sentifargo.gateway.service

import com.sentifargo.gateway.config.FastApiProperties
import com.sentifargo.gateway.config.GatewayProperties
import com.sentifargo.gateway.config.UploadProperties
import com.sentifargo.gateway.model.FinalizeUploadInput
import org.junit.jupiter.api.Assertions.assertThrows
import org.junit.jupiter.api.Test
import org.mockito.Mockito.mock
import software.amazon.awssdk.services.s3.S3Client
import software.amazon.awssdk.services.s3.presigner.S3Presigner

class UploadServiceTests {
    private val props = GatewayProperties(
        fastapi = FastApiProperties(
            baseUrl = "http://localhost:8000",
            timeoutSeconds = 30,
        ),
        uploads = UploadProperties(
            bucket = "test-bucket",
            region = "us-east-1",
            signedUrlMinutes = 15,
            maxBytes = 1024 * 1024,
        ),
    )

    @Test
    fun `finalizeUpload rejects unsupported tool`() {
        val service = UploadService(
            props = props,
            presigner = mock(S3Presigner::class.java),
            s3Client = mock(S3Client::class.java),
        )

        assertThrows(IllegalArgumentException::class.java) {
            service.finalizeUpload(
                FinalizeUploadInput(
                    objectKey = "uploads/1700000/test.png",
                    tool = "unknown-tool",
                    correlationId = "cid-123",
                ),
            )
        }
    }

    @Test
    fun `finalizeUpload rejects keys outside uploads namespace`() {
        val service = UploadService(
            props = props,
            presigner = mock(S3Presigner::class.java),
            s3Client = mock(S3Client::class.java),
        )

        assertThrows(IllegalArgumentException::class.java) {
            service.finalizeUpload(
                FinalizeUploadInput(
                    objectKey = "tmp/test.png",
                    tool = "vision",
                    correlationId = "cid-456",
                ),
            )
        }
    }
}

package com.sentifargo.gateway.graphql

import com.fasterxml.jackson.module.kotlin.jacksonObjectMapper
import com.sentifargo.gateway.config.FastApiProperties
import com.sentifargo.gateway.config.GatewayProperties
import com.sentifargo.gateway.config.UploadProperties
import com.sentifargo.gateway.model.UploadSessionInput
import com.sentifargo.gateway.service.EventStreamService
import com.sentifargo.gateway.service.FastApiClient
import com.sentifargo.gateway.service.UploadService
import graphql.GraphqlErrorException
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import org.junit.jupiter.api.AfterEach
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertThrows
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.Test
import org.mockito.Mockito.mock
import org.springframework.web.reactive.function.client.WebClient
import software.amazon.awssdk.services.s3.S3Client
import software.amazon.awssdk.services.s3.presigner.S3Presigner

class GatewayResolverTests {
    private lateinit var server: MockWebServer
    private lateinit var resolver: GatewayResolver

    @BeforeEach
    fun setUp() {
        server = MockWebServer()
        server.start()
        val webClient = WebClient.builder()
            .baseUrl(server.url("/").toString().trimEnd('/'))
            .build()
        val fastApiClient = FastApiClient(webClient, jacksonObjectMapper())
        val uploadService = UploadService(
            props = GatewayProperties(
                fastapi = FastApiProperties(
                    baseUrl = "http://localhost:8000",
                    timeoutSeconds = 30,
                ),
                uploads = UploadProperties(
                    bucket = "bucket",
                    region = "us-east-1",
                    signedUrlMinutes = 15,
                    maxBytes = 1024 * 1024,
                ),
            ),
            presigner = mock(S3Presigner::class.java),
            s3Client = mock(S3Client::class.java),
        )
        resolver = GatewayResolver(fastApiClient, EventStreamService(), uploadService)
    }

    @AfterEach
    fun tearDown() {
        server.shutdown()
    }

    @Test
    fun `viewer query allows open access when auth header is absent`() {
        server.enqueue(
            MockResponse()
                .setResponseCode(200)
                .setHeader("Content-Type", "application/json")
                .setBody("""{"id":"u1","username":"demo","roles":["viewer"],"is_active":true}"""),
        )

        val out = resolver.viewer(null).block()
        assertEquals("demo", out?.username)

        val request = server.takeRequest()
        assertEquals("/api/v1/users/me", request.path)
    }

    @Test
    fun `systemHealth resolves through backend with auth`() {
        server.enqueue(
            MockResponse()
                .setResponseCode(200)
                .setHeader("Content-Type", "application/json")
                .setBody("""{"status":"ok","service":"api","version":"1.0","uptime_seconds":12.5}"""),
        )

        val health = resolver.systemHealth("Bearer t").block()
        assertEquals("ok", health?.status)
        assertEquals("api", health?.service)
    }

    @Test
    fun `createUploadSession maps validation error to GraphQL error`() {
        val ex = assertThrows(GraphqlErrorException::class.java) {
            resolver.createUploadSession(
                UploadSessionInput(
                    fileName = "sample.bin",
                    contentType = "text/html",
                    maxBytes = 10,
                ),
                "Bearer t",
            )
        }
        assertEquals("Unsupported contentType 'text/html'.", ex.message)
    }

    @Test
    fun `trainingDomain resolves through backend with auth`() {
        server.enqueue(
            MockResponse()
                .setResponseCode(200)
                .setHeader("Content-Type", "application/json")
                .setBody(
                    """
                    {
                      "domain":"fraud",
                      "status":"ready",
                      "datasetReady":true,
                      "modelReady":true,
                      "metrics":{"accuracy":0.99,"f1":0.62,"auc":0.91,"precision":0.55,"recall":0.71},
                      "sourcePath":"experiments/fraud/metrics/metrics.json",
                      "updatedAt":"2026-02-14T00:00:00Z",
                      "blockers":[]
                    }
                    """.trimIndent(),
                ),
        )

        val out = resolver.trainingDomain("fraud", "Bearer token").block()
        assertEquals("fraud", out?.domain)
        assertEquals("ready", out?.status)
        assertEquals(0.99, out?.metrics?.accuracy)

        val request = server.takeRequest()
        assertTrue((request.path ?: "").contains("/api/v1/training/domain/fraud"))
    }
}

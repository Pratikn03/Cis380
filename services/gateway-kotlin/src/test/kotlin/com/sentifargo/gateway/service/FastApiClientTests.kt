package com.sentifargo.gateway.service

import com.fasterxml.jackson.module.kotlin.jacksonObjectMapper
import okhttp3.mockwebserver.Dispatcher
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import okhttp3.mockwebserver.RecordedRequest
import org.junit.jupiter.api.AfterEach
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertNull
import org.junit.jupiter.api.Assertions.assertThrows
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.Test
import org.springframework.web.reactive.function.client.WebClient

class FastApiClientTests {
    private lateinit var server: MockWebServer
    private lateinit var client: FastApiClient

    @BeforeEach
    fun setUp() {
        server = MockWebServer()
        server.start()
        val webClient = WebClient.builder()
            .baseUrl(server.url("/").toString().trimEnd('/'))
            .build()
        client = FastApiClient(webClient, jacksonObjectMapper())
    }

    @AfterEach
    fun tearDown() {
        server.shutdown()
    }

    @Test
    fun `viewer maps optional email as null when missing`() {
        server.enqueue(
            MockResponse()
                .setResponseCode(200)
                .setHeader("Content-Type", "application/json")
                .setBody("""{"id":"u1","username":"alice","roles":["admin"],"is_active":true}"""),
        )

        val viewer = client.viewer("Bearer test-token").block()
        val request = server.takeRequest()

        assertEquals("/api/v1/users/me", request.path)
        assertEquals("Bearer test-token", request.getHeader("Authorization"))
        assertEquals("u1", viewer?.id)
        assertEquals("alice", viewer?.username)
        assertNull(viewer?.email)
    }

    @Test
    fun `scoreFraud maps expectedFeatures as null when backend omits it`() {
        server.enqueue(
            MockResponse()
                .setResponseCode(200)
                .setHeader("Content-Type", "application/json")
                .setBody("""{"score":0.91,"input_features":4}"""),
        )

        val score = client.scoreFraud(listOf(1.0, 2.0, 3.0, 4.0), "Bearer token").block()
        val request = server.takeRequest()

        assertEquals("/api/fraud", request.path)
        assertEquals("POST", request.method)
        assertEquals(0.91, score?.score)
        assertEquals(4, score?.inputFeatures)
        assertNull(score?.expectedFeatures)
    }

    @Test
    fun `ragStatus falls back to unknown when backend errors`() {
        server.enqueue(MockResponse().setResponseCode(500).setBody("boom"))

        val status = client.ragStatus("Bearer token").block()

        assertEquals("unknown", status?.status)
        assertNull(status?.docsCount)
        assertNull(status?.chunksCount)
    }

    @Test
    fun `trainingOverview maps domains and metrics`() {
        server.enqueue(
            MockResponse()
                .setResponseCode(200)
                .setHeader("Content-Type", "application/json")
                .setBody(
                    """
                    {
                      "generatedAt":"2026-02-14T00:00:00Z",
                      "readyCount":1,
                      "totalCount":2,
                      "domains":[
                        {
                          "domain":"fraud",
                          "status":"ready",
                          "datasetReady":true,
                          "modelReady":true,
                          "metrics":{"accuracy":0.99,"f1":0.62,"auc":0.91,"precision":0.55,"recall":0.71},
                          "sourcePath":"experiments/fraud/metrics/metrics.json",
                          "updatedAt":"2026-02-14T00:00:00Z",
                          "blockers":[]
                        },
                        {
                          "domain":"vision",
                          "status":"missing",
                          "datasetReady":false,
                          "modelReady":false,
                          "metrics":null,
                          "sourcePath":"",
                          "updatedAt":null,
                          "blockers":["metrics_missing"]
                        }
                      ]
                    }
                    """.trimIndent(),
                ),
        )

        val out = client.trainingOverview("Bearer token").block()
        val request = server.takeRequest()

        assertEquals("/api/v1/training/overview", request.path)
        assertEquals(1, out?.readyCount)
        assertEquals(2, out?.totalCount)
        assertEquals("fraud", out?.domains?.firstOrNull()?.domain)
        assertEquals(0.91, out?.domains?.firstOrNull()?.metrics?.auc)
        assertEquals("missing", out?.domains?.getOrNull(1)?.status)
    }

    @Test
    fun `dashboardSummary does not fabricate fallback values on backend failure`() {
        server.dispatcher = object : Dispatcher() {
            override fun dispatch(request: RecordedRequest): MockResponse {
                return when {
                    request.path?.startsWith("/api/health") == true -> {
                        MockResponse().setResponseCode(500).setBody("boom")
                    }

                    request.path?.startsWith("/api/v1/jobs") == true -> {
                        MockResponse()
                            .setResponseCode(200)
                            .setHeader("Content-Type", "application/json")
                            .setBody("[]")
                    }

                    request.path?.startsWith("/api/rag/status") == true -> {
                        MockResponse()
                            .setResponseCode(200)
                            .setHeader("Content-Type", "application/json")
                            .setBody("""{"status":"ready","docs_count":10,"chunks_count":100}""")
                    }

                    else -> MockResponse().setResponseCode(404)
                }
            }
        }

        assertThrows(Exception::class.java) {
            client.dashboardSummary("Bearer token").block()
        }
    }
}

package com.sentifargo.gateway.service

import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Test
import reactor.test.StepVerifier

class EventStreamServiceTests {
    private val service = EventStreamService()

    @Test
    fun `jobProgress emits only matching job id`() {
        service.publishJobProgress("job-a", "running", 0.25, "step-1")
        service.publishJobProgress("job-b", "running", 0.5, "step-2")

        StepVerifier.create(service.jobProgress("job-a").take(1))
            .assertNext {
                assertEquals("job-a", it.jobId)
                assertEquals("running", it.status)
                assertEquals(0.25, it.progress)
            }
            .verifyComplete()
    }

    @Test
    fun `inferenceTrace emits published trace event`() {
        service.publishInferenceTrace(
            correlationId = "cid-1",
            step = "risk.features",
            status = "started",
            message = "collecting",
            latencyMs = 10.5,
        )

        StepVerifier.create(service.inferenceTrace("cid-1").take(1))
            .assertNext {
                assertEquals("cid-1", it.correlationId)
                assertEquals("risk.features", it.step)
                assertEquals("started", it.status)
                assertEquals(10.5, it.latencyMs)
            }
            .verifyComplete()
    }

    @Test
    fun `systemAlerts emits alert event`() {
        service.publishSystemAlert(level = "WARN", message = "queue lag", component = "gateway")

        StepVerifier.create(service.systemAlerts().take(1))
            .assertNext {
                assertEquals("WARN", it.level)
                assertEquals("gateway", it.component)
                assertEquals("queue lag", it.message)
            }
            .verifyComplete()
    }
}

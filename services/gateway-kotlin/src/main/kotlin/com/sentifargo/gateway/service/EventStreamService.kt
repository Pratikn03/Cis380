package com.sentifargo.gateway.service

import com.sentifargo.gateway.model.InferenceTraceEvent
import com.sentifargo.gateway.model.JobProgressEvent
import com.sentifargo.gateway.model.SystemAlert
import java.time.Instant
import java.time.format.DateTimeFormatter
import org.springframework.stereotype.Service
import reactor.core.publisher.Flux
import reactor.core.publisher.Sinks

@Service
class EventStreamService {
    private val jobProgressSink = Sinks.many().replay().limit<JobProgressEvent>(200)
    private val traceSink = Sinks.many().replay().limit<InferenceTraceEvent>(500)
    private val alertSink = Sinks.many().replay().limit<SystemAlert>(200)

    fun publishJobProgress(jobId: String, status: String, progress: Double, message: String) {
        jobProgressSink.tryEmitNext(
            JobProgressEvent(
                jobId = jobId,
                status = status,
                progress = progress,
                message = message,
                timestamp = DateTimeFormatter.ISO_INSTANT.format(Instant.now()),
            ),
        )
    }

    fun publishInferenceTrace(
        correlationId: String,
        step: String,
        status: String,
        message: String,
        latencyMs: Double? = null,
    ) {
        traceSink.tryEmitNext(
            InferenceTraceEvent(
                correlationId = correlationId,
                step = step,
                status = status,
                message = message,
                timestamp = DateTimeFormatter.ISO_INSTANT.format(Instant.now()),
                latencyMs = latencyMs,
            ),
        )
    }

    fun publishSystemAlert(level: String, message: String, component: String) {
        alertSink.tryEmitNext(
            SystemAlert(
                level = level,
                message = message,
                component = component,
                timestamp = DateTimeFormatter.ISO_INSTANT.format(Instant.now()),
            ),
        )
    }

    fun jobProgress(jobId: String): Flux<JobProgressEvent> {
        return jobProgressSink.asFlux().filter { it.jobId == jobId }
    }

    fun inferenceTrace(correlationId: String): Flux<InferenceTraceEvent> {
        return traceSink.asFlux().filter { it.correlationId == correlationId }
    }

    fun systemAlerts(): Flux<SystemAlert> {
        return alertSink.asFlux()
    }
}

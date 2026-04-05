package com.sentifargo.gateway.service

class BackendServiceException(
    val status: Int,
    val code: String,
    override val message: String,
    val details: Map<String, Any?> = emptyMap(),
    val correlationId: String? = null,
) : RuntimeException(message)

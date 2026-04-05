package com.sentifargo.gateway.config

import org.springframework.boot.context.properties.ConfigurationProperties

@ConfigurationProperties(prefix = "sentifargo")
data class GatewayProperties(
    val fastapi: FastApiProperties,
    val uploads: UploadProperties,
)

data class FastApiProperties(
    val baseUrl: String,
    val timeoutSeconds: Int,
)

data class UploadProperties(
    val bucket: String,
    val region: String,
    val signedUrlMinutes: Long,
    val maxBytes: Int,
)

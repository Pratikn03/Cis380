package com.sentifargo.gateway.config

import graphql.scalars.ExtendedScalars
import java.time.Duration
import org.springframework.boot.context.properties.EnableConfigurationProperties
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration
import org.springframework.graphql.execution.RuntimeWiringConfigurer
import org.springframework.graphql.server.WebGraphQlInterceptor
import org.springframework.http.HttpHeaders
import org.springframework.http.client.reactive.ReactorClientHttpConnector
import org.springframework.security.config.Customizer
import org.springframework.security.config.annotation.method.configuration.EnableMethodSecurity
import org.springframework.security.config.annotation.web.reactive.EnableWebFluxSecurity
import org.springframework.security.config.web.server.ServerHttpSecurity
import org.springframework.security.web.server.SecurityWebFilterChain
import org.springframework.web.reactive.function.client.WebClient
import reactor.netty.http.client.HttpClient
import software.amazon.awssdk.regions.Region
import software.amazon.awssdk.services.s3.S3Client
import software.amazon.awssdk.services.s3.presigner.S3Presigner

@Configuration
@EnableConfigurationProperties(GatewayProperties::class)
@EnableMethodSecurity
@EnableWebFluxSecurity
class AppConfig {
    @Bean
    fun runtimeWiringConfigurer(): RuntimeWiringConfigurer {
        return RuntimeWiringConfigurer { builder ->
            builder.scalar(ExtendedScalars.Json)
        }
    }

    @Bean
    fun fastApiWebClient(props: GatewayProperties): WebClient {
        val httpClient = HttpClient.create()
            .responseTimeout(Duration.ofSeconds(props.fastapi.timeoutSeconds.toLong()))
        return WebClient.builder()
            .clientConnector(ReactorClientHttpConnector(httpClient))
            .baseUrl(props.fastapi.baseUrl)
            .defaultHeader(HttpHeaders.CONTENT_TYPE, "application/json")
            .build()
    }

    @Bean
    fun s3Client(props: GatewayProperties): S3Client {
        return S3Client.builder().region(Region.of(props.uploads.region)).build()
    }

    @Bean
    fun s3Presigner(props: GatewayProperties): S3Presigner {
        return S3Presigner.builder().region(Region.of(props.uploads.region)).build()
    }

    @Bean
    fun graphQlAuthInterceptor(): WebGraphQlInterceptor {
        return WebGraphQlInterceptor { request, chain ->
            val auth = request.headers.getFirst(HttpHeaders.AUTHORIZATION)
            val reqId = request.headers.getFirst("x-request-id")
            val contextValues = mutableMapOf<String, Any>()
            if (!auth.isNullOrBlank()) {
                contextValues["authToken"] = auth
            }
            if (!reqId.isNullOrBlank()) {
                contextValues["requestId"] = reqId
            }
            request.configureExecutionInput { _, builder ->
                builder.graphQLContext(contextValues).build()
            }
            chain.next(request)
        }
    }

    @Bean
    fun securityFilterChain(http: ServerHttpSecurity): SecurityWebFilterChain {
        http
            .csrf { it.disable() }
            .authorizeExchange {
                it.pathMatchers("/actuator/health", "/actuator/info").permitAll()
                    .pathMatchers("/graphql").permitAll()
                    .anyExchange().authenticated()
            }
            .httpBasic(Customizer.withDefaults())
        return http.build()
    }
}

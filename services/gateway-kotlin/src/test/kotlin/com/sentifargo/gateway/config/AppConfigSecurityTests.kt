package com.sentifargo.gateway.config

import org.junit.jupiter.api.Test
import org.springframework.beans.factory.annotation.Autowired
import org.springframework.boot.test.autoconfigure.web.reactive.AutoConfigureWebTestClient
import org.springframework.boot.test.context.SpringBootTest
import org.springframework.http.MediaType
import org.springframework.test.web.reactive.server.WebTestClient

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@AutoConfigureWebTestClient
class AppConfigSecurityTests {
    @Autowired
    private lateinit var webTestClient: WebTestClient

    @Test
    fun `actuator health is publicly accessible`() {
        webTestClient.get()
            .uri("/actuator/health")
            .exchange()
            .expectStatus().isOk
    }

    @Test
    fun `graphql endpoint is not blocked by security filter`() {
        webTestClient.post()
            .uri("/graphql")
            .contentType(MediaType.APPLICATION_JSON)
            .bodyValue("""{"query":"query{__typename}"}""")
            .exchange()
            .expectStatus().is2xxSuccessful
    }

    @Test
    fun `non-whitelisted route requires authentication`() {
        webTestClient.get()
            .uri("/private")
            .exchange()
            .expectStatus().isUnauthorized
    }
}

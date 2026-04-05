package com.sentifargo.gateway

import org.springframework.boot.autoconfigure.SpringBootApplication
import org.springframework.boot.runApplication

@SpringBootApplication
class SentifargoGatewayApplication

fun main(args: Array<String>) {
    runApplication<SentifargoGatewayApplication>(*args)
}

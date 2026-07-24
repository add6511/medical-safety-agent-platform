package com.medicalsafety.platform.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.web.client.RestClient;

@Configuration
public class AiServiceConfig {

    @Bean("aiRestClient")
    public RestClient aiRestClient(
            RestClient.Builder builder,
            @Value("${ai.service.base-url}") String baseUrl,
            @Value("${ai.service.connect-timeout-ms:3000}") int connectTimeoutMs,
            @Value("${ai.service.read-timeout-ms:15000}") int readTimeoutMs) {

        SimpleClientHttpRequestFactory requestFactory =
                new SimpleClientHttpRequestFactory();

        requestFactory.setConnectTimeout(connectTimeoutMs);
        requestFactory.setReadTimeout(readTimeoutMs);

        return builder
                .baseUrl(baseUrl)
                .requestFactory(requestFactory)
                .defaultHeader(
                        HttpHeaders.CONTENT_TYPE,
                        MediaType.APPLICATION_JSON_VALUE)
                .defaultHeader(
                        HttpHeaders.ACCEPT,
                        MediaType.APPLICATION_JSON_VALUE)
                .build();
    }
}
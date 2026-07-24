package com.medicalsafety.platform.service;

import com.medicalsafety.platform.dto.AiTriageRequest;
import com.medicalsafety.platform.dto.AiTriageResponse;
import com.medicalsafety.platform.exception.BusinessException;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.stereotype.Service;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestClientResponseException;

@Slf4j
@Service
public class AiTriageClient {

    private static final String TRIAGE_PATH =
            "/api/v1/triage/analyze";

    private final RestClient aiRestClient;

    public AiTriageClient(
            @Qualifier("aiRestClient")
            RestClient aiRestClient) {
        this.aiRestClient = aiRestClient;
    }

    public AiTriageResponse analyze(
            AiTriageRequest request,
            String traceId) {

        try {
            AiTriageResponse response = aiRestClient
                    .post()
                    .uri(TRIAGE_PATH)
                    .header("X-Trace-Id", traceId)
                    .body(request)
                    .retrieve()
                    .body(AiTriageResponse.class);

            if (response == null) {
                throw new BusinessException(
                        "AI_SERVICE_EMPTY_RESPONSE",
                        "AI服务返回空响应"
                );
            }

            if (response.getRiskLevel() == null
                    || response.getRiskLevel().isBlank()) {
                throw new BusinessException(
                        "AI_SERVICE_INVALID_RESPONSE",
                        "AI服务响应缺少风险等级"
                );
            }

            log.info(
                    "AI_TRIAGE_SUCCESS | caseId={} | riskLevel={} "
                            + "| safetyStatus={} | traceId={}",
                    response.getCaseId(),
                    response.getRiskLevel(),
                    response.getSafetyStatus(),
                    traceId
            );

            return response;

        } catch (BusinessException e) {
            throw e;

        } catch (RestClientResponseException e) {
            log.warn(
                    "AI_TRIAGE_HTTP_ERROR | status={} | traceId={}",
                    e.getStatusCode().value(),
                    traceId
            );

            throw new BusinessException(
                    "AI_SERVICE_HTTP_ERROR",
                    "AI服务调用失败，HTTP状态码："
                            + e.getStatusCode().value()
            );

        } catch (ResourceAccessException e) {
            log.warn(
                    "AI_TRIAGE_UNAVAILABLE | traceId={} | error={}",
                    traceId,
                    e.getClass().getSimpleName()
            );

            throw new BusinessException(
                    "AI_SERVICE_UNAVAILABLE",
                    "AI服务连接失败或响应超时，请转人工审核"
            );

        } catch (RestClientException e) {
            log.warn(
                    "AI_TRIAGE_CLIENT_ERROR | traceId={} | error={}",
                    traceId,
                    e.getClass().getSimpleName()
            );

            throw new BusinessException(
                    "AI_SERVICE_CALL_FAILED",
                    "AI服务调用异常，请转人工审核"
            );
        }
    }
}
package com.medicalsafety.platform.service;

import com.medicalsafety.platform.dto.AiTriageRequest;
import com.medicalsafety.platform.dto.AiTriageResponse;
import com.medicalsafety.platform.dto.AiTriageSymptomRequest;
import com.medicalsafety.platform.exception.BusinessException;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.test.web.client.MockRestServiceServer;
import org.springframework.web.client.RestClient;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.springframework.test.web.client.ExpectedCount.once;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.content;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.header;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.jsonPath;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.method;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.requestTo;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withStatus;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withSuccess;

class AiTriageClientTest {

    private MockRestServiceServer server;
    private AiTriageClient client;

    @BeforeEach
    void setUp() {
        RestClient.Builder builder = RestClient.builder()
                .baseUrl("http://127.0.0.1:8000");

        server = MockRestServiceServer
                .bindTo(builder)
                .build();

        client = new AiTriageClient(builder.build());
    }

    @Test
    void shouldReturnAiTriageResponseWhenRequestSucceeds() {
        server.expect(
                        once(),
                        requestTo(
                                "http://127.0.0.1:8000"
                                        + "/api/v1/triage/analyze"
                        )
                )
                .andExpect(method(HttpMethod.POST))
                .andExpect(
                        header(
                                "X-Trace-Id",
                                "trace-success-001"
                        )
                )
                .andExpect(
                        content().contentTypeCompatibleWith(
                                MediaType.APPLICATION_JSON
                        )
                )
                .andExpect(
                        jsonPath("$.case_id")
                                .value("SYN-TEST-001")
                )
                .andExpect(
                        jsonPath("$.red_flags[0]")
                                .value(
                                        "persistent_chest_discomfort"
                                )
                )
                .andRespond(
                        withSuccess(
                                """
                                {
                                  "case_id": "SYN-TEST-001",
                                  "trace_id": "ai-trace-001",
                                  "risk_level": "HIGH",
                                  "symptom_summary": "持续胸部不适30分钟",
                                  "red_flags": [
                                    "persistent_chest_discomfort"
                                  ],
                                  "evidence": [],
                                  "citations": [],
                                  "missing_information": [],
                                  "followup_questions": [],
                                  "safety_status": "human_review",
                                  "safety_flags": [],
                                  "sanitized_input": "合成教学病例",
                                  "needs_human_review": true,
                                  "disclaimer": "仅供教学演示"
                                }
                                """,
                                MediaType.APPLICATION_JSON
                        )
                );

        AiTriageResponse response = client.analyze(
                buildRequest(),
                "trace-success-001"
        );

        assertEquals("SYN-TEST-001", response.getCaseId());
        assertEquals("HIGH", response.getRiskLevel());
        assertEquals(
                "human_review",
                response.getSafetyStatus()
        );
        assertTrue(response.getNeedsHumanReview());
        assertEquals(
                List.of("persistent_chest_discomfort"),
                response.getRedFlags()
        );

        server.verify();
    }

    @Test
    void shouldRejectResponseWithoutRiskLevel() {
        server.expect(
                        once(),
                        requestTo(
                                "http://127.0.0.1:8000"
                                        + "/api/v1/triage/analyze"
                        )
                )
                .andRespond(
                        withSuccess(
                                """
                                {
                                  "case_id": "SYN-TEST-001",
                                  "trace_id": "ai-trace-invalid"
                                }
                                """,
                                MediaType.APPLICATION_JSON
                        )
                );

        BusinessException exception = assertThrows(
                BusinessException.class,
                () -> client.analyze(
                        buildRequest(),
                        "trace-invalid-001"
                )
        );

        assertEquals(
                "AI_SERVICE_INVALID_RESPONSE",
                exception.getErrorCode()
        );

        server.verify();
    }

    @Test
    void shouldConvertHttpErrorToBusinessException() {
        server.expect(
                        once(),
                        requestTo(
                                "http://127.0.0.1:8000"
                                        + "/api/v1/triage/analyze"
                        )
                )
                .andRespond(
                        withStatus(
                                HttpStatus.SERVICE_UNAVAILABLE
                        )
                                .contentType(
                                        MediaType.APPLICATION_JSON
                                )
                                .body(
                                        """
                                        {
                                          "detail": "分诊服务未初始化"
                                        }
                                        """
                                )
                );

        BusinessException exception = assertThrows(
                BusinessException.class,
                () -> client.analyze(
                        buildRequest(),
                        "trace-http-error-001"
                )
        );

        assertEquals(
                "AI_SERVICE_HTTP_ERROR",
                exception.getErrorCode()
        );

        server.verify();
    }

    private AiTriageRequest buildRequest() {
        return AiTriageRequest.builder()
                .caseId("SYN-TEST-001")
                .age(45)
                .symptoms(
                        List.of(
                                AiTriageSymptomRequest.builder()
                                        .name("持续胸部不适")
                                        .severity(9)
                                        .duration("30分钟")
                                        .build()
                        )
                )
                .redFlags(
                        List.of(
                                "persistent_chest_discomfort"
                        )
                )
                .freeText("合成教学病例")
                .modelSuggestedRisk("LOW")
                .build();
    }
}
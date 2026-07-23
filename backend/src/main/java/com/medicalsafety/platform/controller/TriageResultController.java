package com.medicalsafety.platform.controller;

import com.medicalsafety.platform.dto.*;
import com.medicalsafety.platform.service.TriageResultService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/v1/triage-results")
@RequiredArgsConstructor
@Tag(name = "分诊结果管理", description = "分诊结果和Agent执行记录接口")
public class TriageResultController {

    private final TriageResultService triageResultService;

    @PostMapping
    @Operation(summary = "创建分诊结果", description = "保存AI分诊结果、引用来源")
    public ResponseEntity<TriageResultResponse> createTriageResult(
            @Valid @RequestBody CreateTriageResultRequest request) {
        Long operatorId = getCurrentUserId();
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(triageResultService.createTriageResult(request, operatorId));
    }

    @GetMapping("/pre-consultation/{preConsultationId}")
    @Operation(summary = "获取分诊结果", description = "根据预问诊ID获取分诊结果")
    public ResponseEntity<TriageResultResponse> getByPreConsultation(@PathVariable Long preConsultationId) {
        return ResponseEntity.ok(triageResultService.getTriageResultByPreConsultation(preConsultationId));
    }

    @PostMapping("/agent-logs")
    @Operation(summary = "创建Agent执行记录", description = "保存Agent执行日志")
    public ResponseEntity<AgentExecutionLogResponse> createAgentLog(
            @Valid @RequestBody CreateAgentExecutionLogRequest request) {
        Long operatorId = getCurrentUserId();
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(triageResultService.createAgentExecutionLog(request, operatorId));
    }

    @GetMapping("/agent-logs/{preConsultationId}")
    @Operation(summary = "获取Agent执行记录", description = "根据预问诊ID获取Agent执行日志")
    public ResponseEntity<List<AgentExecutionLogResponse>> getAgentLogs(
            @PathVariable Long preConsultationId) {
        return ResponseEntity.ok(triageResultService.getAgentExecutionLogs(preConsultationId));
    }

    private Long getCurrentUserId() {
        return (Long) SecurityContextHolder.getContext().getAuthentication().getPrincipal();
    }
}
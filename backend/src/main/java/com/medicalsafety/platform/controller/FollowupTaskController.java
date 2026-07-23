package com.medicalsafety.platform.controller;

import com.medicalsafety.platform.dto.*;
import com.medicalsafety.platform.service.FollowupTaskService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/v1/followup-tasks")
@RequiredArgsConstructor
@Tag(name = "随访任务管理", description = "随访任务分配和处理接口")
public class FollowupTaskController {

    private final FollowupTaskService followupTaskService;

    @PostMapping
    @Operation(summary = "分配随访任务", description = "医务人员分配随访任务给随访人员")
    public ResponseEntity<FollowupTaskResponse> createTask(@Valid @RequestBody CreateFollowupTaskRequest request) {
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(followupTaskService.createTask(request, getCurrentUserId(), getCurrentRoles()));
    }

    @GetMapping("/my")
    @Operation(summary = "查看我的任务", description = "随访人员查看分配给自己的任务")
    public ResponseEntity<List<FollowupTaskResponse>> getMyTasks() {
        return ResponseEntity.ok(followupTaskService.getMyTasks(getCurrentUserId(), getCurrentRoles()));
    }

    @GetMapping("/{id}")
    @Operation(summary = "获取任务详情", description = "获取随访任务详情")
    public ResponseEntity<FollowupTaskResponse> getTask(@PathVariable Long id) {
        return ResponseEntity.ok(followupTaskService.getTask(id, getCurrentUserId(), getCurrentRoles()));
    }

    @PutMapping
    @Operation(summary = "更新任务状态", description = "随访人员更新任务状态或备注")
    public ResponseEntity<FollowupTaskResponse> updateTask(@Valid @RequestBody UpdateFollowupTaskRequest request) {
        return ResponseEntity.ok(followupTaskService.updateTask(request, getCurrentUserId(), getCurrentRoles()));
    }

    private Long getCurrentUserId() {
        return (Long) SecurityContextHolder.getContext().getAuthentication().getPrincipal();
    }

    private List<String> getCurrentRoles() {
        return SecurityContextHolder.getContext().getAuthentication().getAuthorities().stream()
                .map(GrantedAuthority::getAuthority)
                .map(a -> a.startsWith("ROLE_") ? a.substring(5) : a)
                .toList();
    }
}
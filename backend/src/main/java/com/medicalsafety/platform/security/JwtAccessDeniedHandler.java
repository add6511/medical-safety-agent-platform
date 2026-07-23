package com.medicalsafety.platform.security;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.medicalsafety.platform.dto.ErrorResponse;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.MediaType;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.web.access.AccessDeniedHandler;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.time.LocalDateTime;
import java.util.UUID;

@Slf4j
@Component
@RequiredArgsConstructor
public class JwtAccessDeniedHandler implements AccessDeniedHandler {

    private final ObjectMapper objectMapper;

    @Override
    public void handle(HttpServletRequest request,
                       HttpServletResponse response,
                       AccessDeniedException accessDeniedException) throws IOException {
        String traceId = UUID.randomUUID().toString();
        log.warn("Access denied: path={}, traceId={}", request.getRequestURI(), traceId);

        response.setStatus(HttpServletResponse.SC_FORBIDDEN);
        response.setContentType(MediaType.APPLICATION_JSON_VALUE);
        response.setCharacterEncoding("UTF-8");

        ErrorResponse errorResponse = ErrorResponse.builder()
                .timestamp(LocalDateTime.now())
                .status(403)
                .errorCode("FORBIDDEN")
                .message("权限不足")
                .path(request.getRequestURI())
                .traceId(traceId)
                .build();

        response.getWriter().write(objectMapper.writeValueAsString(errorResponse));
    }
}
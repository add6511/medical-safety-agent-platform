package com.medicalsafety.platform.security;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.medicalsafety.platform.dto.ErrorResponse;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.MediaType;
import org.springframework.security.core.AuthenticationException;
import org.springframework.security.web.AuthenticationEntryPoint;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.time.LocalDateTime;
import java.util.UUID;

@Slf4j
@Component
@RequiredArgsConstructor
public class JwtAuthenticationEntryPoint implements AuthenticationEntryPoint {

    private final ObjectMapper objectMapper;

    @Override
    public void commence(HttpServletRequest request,
                         HttpServletResponse response,
                         AuthenticationException authException) throws IOException {
        String traceId = UUID.randomUUID().toString();
        log.warn("Unauthorized access: path={}, traceId={}", request.getRequestURI(), traceId);

        response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
        response.setContentType(MediaType.APPLICATION_JSON_VALUE);
        response.setCharacterEncoding("UTF-8");

        ErrorResponse errorResponse = ErrorResponse.builder()
                .timestamp(LocalDateTime.now())
                .status(401)
                .errorCode("UNAUTHORIZED")
                .message("未登录或Token已过期")
                .path(request.getRequestURI())
                .traceId(traceId)
                .build();

        response.getWriter().write(objectMapper.writeValueAsString(errorResponse));
    }
}
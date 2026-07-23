package com.medicalsafety.platform.exception;

import com.medicalsafety.platform.dto.ErrorResponse;
import jakarta.servlet.http.HttpServletRequest;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.core.AuthenticationException;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.time.LocalDateTime;
import java.util.UUID;

@Slf4j
@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ErrorResponse> handleValidation(MethodArgumentNotValidException ex,
                                                          HttpServletRequest request) {
        String traceId = UUID.randomUUID().toString();
        String message = ex.getBindingResult().getFieldErrors().stream()
                .map(FieldError::getDefaultMessage)
                .reduce((a, b) -> a + "; " + b)
                .orElse("参数校验失败");

        log.warn("Validation error: path={}, message={}, traceId={}", request.getRequestURI(), message, traceId);

        ErrorResponse response = ErrorResponse.builder()
                .timestamp(LocalDateTime.now())
                .status(400)
                .errorCode("VALIDATION_ERROR")
                .message(message)
                .path(request.getRequestURI())
                .traceId(traceId)
                .build();

        return ResponseEntity.badRequest().body(response);
    }

    @ExceptionHandler(AuthenticationException.class)
    public ResponseEntity<ErrorResponse> handleAuthentication(AuthenticationException ex,
                                                              HttpServletRequest request) {
        String traceId = UUID.randomUUID().toString();
        log.warn("Authentication error: path={}, traceId={}", request.getRequestURI(), traceId);

        ErrorResponse response = ErrorResponse.builder()
                .timestamp(LocalDateTime.now())
                .status(401)
                .errorCode("AUTHENTICATION_FAILED")
                .message("用户名或密码错误")
                .path(request.getRequestURI())
                .traceId(traceId)
                .build();

        return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(response);
    }

    @ExceptionHandler(com.medicalsafety.platform.exception.AuthenticationException.class)
    public ResponseEntity<ErrorResponse> handleCustomAuthentication(
            com.medicalsafety.platform.exception.AuthenticationException ex,
            HttpServletRequest request) {
        String traceId = UUID.randomUUID().toString();
        log.warn("Authentication error: path={}, traceId={}", request.getRequestURI(), traceId);

        ErrorResponse response = ErrorResponse.builder()
                .timestamp(LocalDateTime.now())
                .status(401)
                .errorCode("AUTHENTICATION_FAILED")
                .message("用户名或密码错误")
                .path(request.getRequestURI())
                .traceId(traceId)
                .build();

        return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(response);
    }

    @ExceptionHandler(AccessDeniedException.class)
    public ResponseEntity<ErrorResponse> handleAccessDenied(AccessDeniedException ex,
                                                            HttpServletRequest request) {
        String traceId = UUID.randomUUID().toString();
        log.warn("Access denied: path={}, traceId={}", request.getRequestURI(), traceId);

        ErrorResponse response = ErrorResponse.builder()
                .timestamp(LocalDateTime.now())
                .status(403)
                .errorCode("ACCESS_DENIED")
                .message("权限不足")
                .path(request.getRequestURI())
                .traceId(traceId)
                .build();

        return ResponseEntity.status(HttpStatus.FORBIDDEN).body(response);
    }

    @ExceptionHandler(com.medicalsafety.platform.exception.AccessDeniedException.class)
    public ResponseEntity<ErrorResponse> handleCustomAccessDenied(
            com.medicalsafety.platform.exception.AccessDeniedException ex,
            HttpServletRequest request) {
        String traceId = UUID.randomUUID().toString();
        log.warn("Access denied: path={}, traceId={}", request.getRequestURI(), traceId);

        ErrorResponse response = ErrorResponse.builder()
                .timestamp(LocalDateTime.now())
                .status(403)
                .errorCode("ACCESS_DENIED")
                .message("权限不足")
                .path(request.getRequestURI())
                .traceId(traceId)
                .build();

        return ResponseEntity.status(HttpStatus.FORBIDDEN).body(response);
    }

    @ExceptionHandler(ResourceNotFoundException.class)
    public ResponseEntity<ErrorResponse> handleNotFound(ResourceNotFoundException ex,
                                                         HttpServletRequest request) {
        String traceId = UUID.randomUUID().toString();
        log.warn("Resource not found: path={}, traceId={}", request.getRequestURI(), traceId);

        ErrorResponse response = ErrorResponse.builder()
                .timestamp(LocalDateTime.now())
                .status(404)
                .errorCode("RESOURCE_NOT_FOUND")
                .message(ex.getMessage())
                .path(request.getRequestURI())
                .traceId(traceId)
                .build();

        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(response);
    }

    @ExceptionHandler(BusinessException.class)
    public ResponseEntity<ErrorResponse> handleBusiness(BusinessException ex,
                                                        HttpServletRequest request) {
        String traceId = UUID.randomUUID().toString();
        log.warn("Business error: path={}, code={}, traceId={}", request.getRequestURI(), ex.getErrorCode(), traceId);

        HttpStatus status = "CONCURRENT_MODIFICATION".equals(ex.getErrorCode()) ? HttpStatus.CONFLICT : HttpStatus.BAD_REQUEST;

        ErrorResponse response = ErrorResponse.builder()
                .timestamp(LocalDateTime.now())
                .status(status.value())
                .errorCode(ex.getErrorCode())
                .message(ex.getMessage())
                .path(request.getRequestURI())
                .traceId(traceId)
                .build();

        return ResponseEntity.status(status).body(response);
    }

    @ExceptionHandler(org.springframework.dao.OptimisticLockingFailureException.class)
    public ResponseEntity<ErrorResponse> handleOptimisticLock(org.springframework.dao.OptimisticLockingFailureException ex,
                                                              HttpServletRequest request) {
        String traceId = UUID.randomUUID().toString();
        log.warn("Concurrent modification: path={}, traceId={}", request.getRequestURI(), traceId);

        ErrorResponse response = ErrorResponse.builder()
                .timestamp(LocalDateTime.now())
                .status(409)
                .errorCode("CONCURRENT_MODIFICATION")
                .message("数据已被其他操作修改，请刷新后重试")
                .path(request.getRequestURI())
                .traceId(traceId)
                .build();

        return ResponseEntity.status(HttpStatus.CONFLICT).body(response);
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ErrorResponse> handleUnknown(Exception ex,
                                                       HttpServletRequest request) {
        String traceId = UUID.randomUUID().toString();
        log.error("Unexpected error: path={}, traceId={}", request.getRequestURI(), traceId, ex);

        ErrorResponse response = ErrorResponse.builder()
                .timestamp(LocalDateTime.now())
                .status(500)
                .errorCode("INTERNAL_ERROR")
                .message("服务器内部错误")
                .path(request.getRequestURI())
                .traceId(traceId)
                .build();

        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(response);
    }
}
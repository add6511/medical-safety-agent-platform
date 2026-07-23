package com.medicalsafety.platform.security;

import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

@Slf4j
@Component
public class SecurityAuditLogger {

    public void logLoginSuccess(String username) {
        log.info("SECURITY_AUDIT | event=LOGIN_SUCCESS | user={}", username);
    }

    public void logLoginFailed(String username, String reason) {
        log.info("SECURITY_AUDIT | event=LOGIN_FAILED | user={} | reason={}", username, reason);
    }

    public void logDisabledUserLogin(String username) {
        log.warn("SECURITY_AUDIT | event=DISABLED_USER_LOGIN_ATTEMPT | user={}", username);
    }

    public void logAccessDenied(String username, String path) {
        log.warn("SECURITY_AUDIT | event=ACCESS_DENIED | user={} | path={}", username, path);
    }
}
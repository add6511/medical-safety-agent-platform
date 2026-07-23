package com.medicalsafety.platform.security;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

class JwtTokenProviderTest {

    private JwtTokenProvider jwtTokenProvider;

    private static final String VALID_SECRET = "dGVzdC1qd3Qtc2VjcmV0LWtleS1mb3ItdGVzdGluZy1wdXJwb3Nlcy1vbmx5LWF0LWxlYXN0LTI1Ni1iaXRz";

    @BeforeEach
    void setUp() {
        jwtTokenProvider = new JwtTokenProvider(VALID_SECRET, 86400000L);
    }

    @Test
    void generateToken() {
        String token = jwtTokenProvider.generateToken(1L, "testuser", List.of("ADMIN"));
        assertNotNull(token);
        assertFalse(token.isEmpty());
    }

    @Test
    void getUsernameFromToken() {
        String token = jwtTokenProvider.generateToken(1L, "testuser", List.of("ADMIN"));
        assertEquals("testuser", jwtTokenProvider.getUsernameFromToken(token));
    }

    @Test
    void getUserIdFromToken() {
        String token = jwtTokenProvider.generateToken(1L, "testuser", List.of("ADMIN"));
        assertEquals(1L, jwtTokenProvider.getUserIdFromToken(token));
    }

    @Test
    void getRolesFromToken() {
        String token = jwtTokenProvider.generateToken(1L, "testuser", List.of("ADMIN", "MEDICAL_STAFF"));
        List<String> roles = jwtTokenProvider.getRolesFromToken(token);
        assertEquals(2, roles.size());
        assertTrue(roles.contains("ADMIN"));
        assertTrue(roles.contains("MEDICAL_STAFF"));
    }

    @Test
    void validateValidToken() {
        String token = jwtTokenProvider.generateToken(1L, "testuser", List.of("ADMIN"));
        assertTrue(jwtTokenProvider.validateToken(token));
    }

    @Test
    void rejectInvalidToken() {
        assertFalse(jwtTokenProvider.validateToken("invalid.token.here"));
    }

    @Test
    void rejectEmptyToken() {
        assertFalse(jwtTokenProvider.validateToken(""));
    }

    @Test
    void rejectNullToken() {
        assertFalse(jwtTokenProvider.validateToken(null));
    }

    @Test
    void rejectExpiredToken() {
        JwtTokenProvider shortLived = new JwtTokenProvider(VALID_SECRET, 0L);
        String token = shortLived.generateToken(1L, "testuser", List.of("ADMIN"));
        assertFalse(shortLived.validateToken(token));
    }

    @Test
    void rejectTamperedToken() {
        String token = jwtTokenProvider.generateToken(1L, "testuser", List.of("ADMIN"));
        assertFalse(jwtTokenProvider.validateToken(token + "tampered"));
    }

    @Test
    void rejectBlankSecret() {
        IllegalStateException ex = assertThrows(IllegalStateException.class,
                () -> new JwtTokenProvider("", 86400000L));
        assertTrue(ex.getMessage().contains("JWT密钥未配置"));
    }

    @Test
    void rejectNullSecret() {
        IllegalStateException ex = assertThrows(IllegalStateException.class,
                () -> new JwtTokenProvider(null, 86400000L));
        assertTrue(ex.getMessage().contains("JWT密钥未配置"));
    }

    @Test
    void rejectShortSecret() {
        IllegalStateException ex = assertThrows(IllegalStateException.class,
                () -> new JwtTokenProvider("short", 86400000L));
        assertTrue(ex.getMessage().contains("JWT密钥长度不足"));
    }
}

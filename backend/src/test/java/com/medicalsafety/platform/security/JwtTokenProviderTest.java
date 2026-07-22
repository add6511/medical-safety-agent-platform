package com.medicalsafety.platform.security;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

class JwtTokenProviderTest {

    private JwtTokenProvider jwtTokenProvider;

    @BeforeEach
    void setUp() {
        String secret = "dGVzdC1qd3Qtc2VjcmV0LWtleS1mb3ItdGVzdGluZy1wdXJwb3Nlcy1vbmx5LWF0LWxlYXN0LTI1Ni1iaXRz";
        long expiration = 86400000L;
        jwtTokenProvider = new JwtTokenProvider(secret, expiration);
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
        String username = jwtTokenProvider.getUsernameFromToken(token);
        assertEquals("testuser", username);
    }

    @Test
    void getUserIdFromToken() {
        String token = jwtTokenProvider.generateToken(1L, "testuser", List.of("ADMIN"));
        Long userId = jwtTokenProvider.getUserIdFromToken(token);
        assertEquals(1L, userId);
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
        JwtTokenProvider shortLivedProvider = new JwtTokenProvider(
                "dGVzdC1qd3Qtc2VjcmV0LWtleS1mb3ItdGVzdGluZy1wdXJwb3Nlcy1vbmx5LWF0LWxlYXN0LTI1Ni1iaXRz",
                0L);
        String token = shortLivedProvider.generateToken(1L, "testuser", List.of("ADMIN"));
        assertFalse(shortLivedProvider.validateToken(token));
    }

    @Test
    void rejectTamperedToken() {
        String token = jwtTokenProvider.generateToken(1L, "testuser", List.of("ADMIN"));
        String tampered = token + "tampered";
        assertFalse(jwtTokenProvider.validateToken(tampered));
    }
}
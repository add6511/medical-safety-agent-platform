package com.medicalsafety.platform.security;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;

import static org.junit.jupiter.api.Assertions.*;

class BCryptPasswordEncoderTest {

    private PasswordEncoder passwordEncoder;

    @BeforeEach
    void setUp() {
        passwordEncoder = new BCryptPasswordEncoder();
    }

    @Test
    void encodePassword() {
        String rawPassword = "password123";
        String encoded = passwordEncoder.encode(rawPassword);
        assertNotNull(encoded);
        assertNotEquals(rawPassword, encoded);
        assertTrue(encoded.startsWith("$2a$"));
    }

    @Test
    void matchPassword() {
        String rawPassword = "password123";
        String encoded = passwordEncoder.encode(rawPassword);
        assertTrue(passwordEncoder.matches(rawPassword, encoded));
    }

    @Test
    void mismatchPassword() {
        String rawPassword = "password123";
        String encoded = passwordEncoder.encode(rawPassword);
        assertFalse(passwordEncoder.matches("wrongPassword", encoded));
    }

    @Test
    void differentEncodingsForSamePassword() {
        String rawPassword = "password123";
        String encoded1 = passwordEncoder.encode(rawPassword);
        String encoded2 = passwordEncoder.encode(rawPassword);
        assertNotEquals(encoded1, encoded2);
    }
}
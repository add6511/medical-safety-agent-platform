package com.medicalsafety.platform.config;

import com.medicalsafety.platform.repository.UserRepository;
import com.medicalsafety.platform.repository.UserRoleRepository;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.transaction.annotation.Transactional;

import static org.junit.jupiter.api.Assertions.*;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
@Transactional
class DemoDataInitializerTest {

    @Autowired
    private UserRepository userRepository;

    @Test
    void demoInitializerNotActiveInTestProfile() {
        assertFalse(userRepository.existsByUsername("demo_patient"));
        assertFalse(userRepository.existsByUsername("demo_admin"));
    }
}
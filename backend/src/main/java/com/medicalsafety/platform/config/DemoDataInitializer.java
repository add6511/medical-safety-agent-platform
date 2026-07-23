package com.medicalsafety.platform.config;

import com.medicalsafety.platform.entity.Role;
import com.medicalsafety.platform.entity.User;
import com.medicalsafety.platform.entity.UserRole;
import com.medicalsafety.platform.enums.RoleType;
import com.medicalsafety.platform.enums.UserStatus;
import com.medicalsafety.platform.repository.RoleRepository;
import com.medicalsafety.platform.repository.UserRepository;
import com.medicalsafety.platform.repository.UserRoleRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.CommandLineRunner;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Profile;
import org.springframework.security.crypto.password.PasswordEncoder;

@Configuration
@Profile("demo")
@RequiredArgsConstructor
@Slf4j
public class DemoDataInitializer {

    private final UserRepository userRepository;
    private final RoleRepository roleRepository;
    private final UserRoleRepository userRoleRepository;
    private final PasswordEncoder passwordEncoder;

    @Bean
    public CommandLineRunner initDemoData() {
        return args -> {
            log.info("SECURITY_AUDIT | event=DEMO_DATA_INIT_START | profile=demo");

            createDemoUserIfAbsent("demo_patient", "demo123", "合成患者A", "CASE-P001", RoleType.PATIENT);
            createDemoUserIfAbsent("demo_medical", "demo123", "合成医生B", "CASE-M001", RoleType.MEDICAL_STAFF);
            createDemoUserIfAbsent("demo_followup", "demo123", "合成随访员C", "CASE-F001", RoleType.FOLLOWUP_STAFF);
            createDemoUserIfAbsent("demo_admin", "demo123", "合成管理员D", "CASE-A001", RoleType.ADMIN);
            createDemoUserIfAbsent("demo_ai_service", "demo123", "AI服务", null, RoleType.AI_SERVICE);

            log.info("SECURITY_AUDIT | event=DEMO_DATA_INIT_COMPLETE | profile=demo");
        };
    }

    private void createDemoUserIfAbsent(String username, String password,
                                         String displayName, String caseCode, RoleType roleType) {
        if (userRepository.existsByUsername(username)) {
            log.info("SECURITY_AUDIT | event=DEMO_USER_SKIP | user={} | reason=already_exists", username);
            return;
        }

        User user = userRepository.save(User.builder()
                .username(username)
                .passwordHash(passwordEncoder.encode(password))
                .displayName(displayName)
                .caseCode(caseCode)
                .status(UserStatus.ENABLED)
                .build());

        Role role = roleRepository.findByName(roleType)
                .orElseThrow(() -> new IllegalStateException("角色不存在: " + roleType));

        userRoleRepository.save(UserRole.builder()
                .user(user)
                .role(role)
                .build());

        log.info("SECURITY_AUDIT | event=DEMO_USER_CREATED | user={} | role={}", username, roleType);
    }
}
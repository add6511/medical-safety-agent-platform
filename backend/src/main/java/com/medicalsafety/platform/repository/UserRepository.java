package com.medicalsafety.platform.repository;

import com.medicalsafety.platform.entity.User;
import com.medicalsafety.platform.enums.UserStatus;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface UserRepository extends JpaRepository<User, Long> {

    Optional<User> findByUsername(String username);

    boolean existsByUsername(String username);

    Optional<User> findByUsernameAndStatus(String username, UserStatus status);
}
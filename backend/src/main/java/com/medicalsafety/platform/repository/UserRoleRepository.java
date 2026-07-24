package com.medicalsafety.platform.repository;

import com.medicalsafety.platform.entity.UserRole;
import org.springframework.data.jpa.repository.EntityGraph;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface UserRoleRepository extends JpaRepository<UserRole, Long> {

    @EntityGraph(attributePaths = "role")
    List<UserRole> findByUserId(Long userId);

    void deleteByUserId(Long userId);
}
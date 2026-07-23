package com.medicalsafety.platform.security;

import com.medicalsafety.platform.entity.User;
import com.medicalsafety.platform.entity.UserRole;
import com.medicalsafety.platform.enums.UserStatus;
import com.medicalsafety.platform.repository.UserRepository;
import com.medicalsafety.platform.repository.UserRoleRepository;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.List;
import java.util.UUID;

@Slf4j
@Component
@RequiredArgsConstructor
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    private static final String AUTHORIZATION_HEADER = "Authorization";
    private static final String BEARER_PREFIX = "Bearer ";
    private static final String TRACE_ID_HEADER = "X-Trace-Id";

    private final JwtTokenProvider jwtTokenProvider;
    private final UserRepository userRepository;
    private final UserRoleRepository userRoleRepository;

    @Override
    protected void doFilterInternal(HttpServletRequest request,
                                    HttpServletResponse response,
                                    FilterChain filterChain) throws ServletException, IOException {
        String traceId = request.getHeader(TRACE_ID_HEADER);
        if (traceId == null || traceId.isBlank()) {
            traceId = UUID.randomUUID().toString();
        }
        request.setAttribute("traceId", traceId);
        response.setHeader(TRACE_ID_HEADER, traceId);

        String token = extractToken(request);

        if (StringUtils.hasText(token) && jwtTokenProvider.validateToken(token)) {
            Long userId = jwtTokenProvider.getUserIdFromToken(token);
            String username = jwtTokenProvider.getUsernameFromToken(token);

            User user = userRepository.findById(userId).orElse(null);

            if (user == null || user.getStatus() != UserStatus.ENABLED) {
                log.warn("SECURITY_AUDIT | event=DISABLED_USER_REQUEST | user={} | traceId={}", username, traceId);
                SecurityContextHolder.clearContext();
                filterChain.doFilter(request, response);
                return;
            }

            List<UserRole> userRoles = userRoleRepository.findByUserId(userId);
            List<SimpleGrantedAuthority> authorities = userRoles.stream()
                    .map(ur -> new SimpleGrantedAuthority("ROLE_" + ur.getRole().getName().name()))
                    .toList();

            UsernamePasswordAuthenticationToken authentication =
                    new UsernamePasswordAuthenticationToken(userId, null, authorities);
            authentication.setDetails(username);

            SecurityContextHolder.getContext().setAuthentication(authentication);
        }

        filterChain.doFilter(request, response);
    }

    private String extractToken(HttpServletRequest request) {
        String bearerToken = request.getHeader(AUTHORIZATION_HEADER);
        if (StringUtils.hasText(bearerToken) && bearerToken.startsWith(BEARER_PREFIX)) {
            return bearerToken.substring(BEARER_PREFIX.length());
        }
        return null;
    }
}

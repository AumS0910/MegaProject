package com.aibrochure.security;

import com.aibrochure.entity.User;
import com.aibrochure.repository.UserRepository;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Slf4j
@Service
public class CustomUserDetailsService implements UserDetailsService {

    @Autowired
    private UserRepository userRepository;

    @Override
    @Transactional
    public UserDetails loadUserByUsername(String email) throws UsernameNotFoundException {
        try {
            log.info("Loading user by email: {}", email);
            User user = userRepository.findByEmail(email)
                    .orElseThrow(() -> new UsernameNotFoundException("User not found with email : " + email));
            log.info("User found: {}", user.getEmail());
            return UserPrincipal.create(user);
        } catch (Exception e) {
            log.error("Error loading user by email: " + email, e);
            throw e;
        }
    }

    @Transactional
    public UserDetails loadUserById(Long id) {
        try {
            log.info("Loading user by id: {}", id);
            User user = userRepository.findById(id)
                    .orElseThrow(() -> new UsernameNotFoundException("User not found with id : " + id));
            log.info("User found: {}", user.getEmail());
            return UserPrincipal.create(user);
        } catch (Exception e) {
            log.error("Error loading user by id: " + id, e);
            throw e;
        }
    }
}

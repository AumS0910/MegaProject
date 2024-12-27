package com.aibrochure.repository;

import com.aibrochure.entity.Brochure;
import com.aibrochure.entity.User;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface BrochureRepository extends JpaRepository<Brochure, Long> {
    Page<Brochure> findByUserOrderByCreatedAtDesc(User user, Pageable pageable);
    Page<Brochure> findByUserAndTitleContainingIgnoreCaseOrderByCreatedAtDesc(User user, String title, Pageable pageable);

    Page<Brochure> findByTitleContainingIgnoreCase(String title, Pageable pageable);
}

package com.aibrochure.controller;

import com.aibrochure.dto.BrochureRequest;
import com.aibrochure.dto.BrochureResponse;
import com.aibrochure.entity.Brochure;
import com.aibrochure.service.BrochureService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@Slf4j
@RestController
@RequestMapping("/api/brochures")
@RequiredArgsConstructor
@CrossOrigin(origins = "*", allowedHeaders = "*")
public class BrochureController {
    
    private final BrochureService brochureService;

    @PostMapping("/generate")
    public ResponseEntity<?> generateBrochure(@Valid @RequestBody BrochureRequest request) {
        try {
            log.info("Received brochure generation request: {}", request);
            Map<String, Object> response = brochureService.startBrochureGeneration(request);
            log.info("Generated brochure response: {}", response);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("Error generating brochure: ", e);
            return ResponseEntity.internalServerError()
                .body(Map.of(
                    "error", "Failed to generate brochure",
                    "message", e.getMessage()
                ));
        }
    }

    @GetMapping("/task-status/{taskId}")
    public ResponseEntity<?> getTaskStatus(@PathVariable String taskId) {
        try {
            log.info("Checking task status for ID: {}", taskId);
            Map<String, Object> status = brochureService.getTaskStatus(taskId);
            log.info("Task status: {}", status);
            return ResponseEntity.ok(status);
        } catch (Exception e) {
            log.error("Error getting task status: ", e);
            return ResponseEntity.internalServerError()
                .body(Map.of(
                    "error", "Failed to get task status",
                    "message", e.getMessage()
                ));
        }
    }

    @GetMapping
    public ResponseEntity<Page<Brochure>> getAllBrochures(
            @RequestParam(required = false) String search,
            Pageable pageable) {
        try {
            log.info("Getting all brochures with search: {}", search);
            return ResponseEntity.ok(brochureService.getAllBrochures(search, pageable));
        } catch (Exception e) {
            log.error("Error getting brochures: ", e);
            throw e;
        }
    }

    @GetMapping("/{id}")
    public ResponseEntity<?> getBrochureById(@PathVariable Long id) {
        try {
            log.info("Getting brochure by ID: {}", id);
            return brochureService.getBrochureById(id)
                    .map(ResponseEntity::ok)
                    .orElse(ResponseEntity.notFound().build());
        } catch (Exception e) {
            log.error("Error getting brochure: ", e);
            return ResponseEntity.internalServerError()
                .body(Map.of(
                    "error", "Failed to get brochure",
                    "message", e.getMessage()
                ));
        }
    }

    @PostMapping
    public ResponseEntity<?> createBrochure(@Valid @RequestBody Brochure brochure) {
        try {
            log.info("Creating brochure: {}", brochure);
            return ResponseEntity.ok(brochureService.createBrochure(brochure));
        } catch (Exception e) {
            log.error("Error creating brochure: ", e);
            return ResponseEntity.internalServerError()
                .body(Map.of(
                    "error", "Failed to create brochure",
                    "message", e.getMessage()
                ));
        }
    }

    @PutMapping("/{id}")
    public ResponseEntity<?> updateBrochure(
            @PathVariable Long id,
            @Valid @RequestBody Brochure brochure) {
        try {
            log.info("Updating brochure ID {}: {}", id, brochure);
            return ResponseEntity.ok(brochureService.updateBrochure(id, brochure));
        } catch (Exception e) {
            log.error("Error updating brochure: ", e);
            return ResponseEntity.internalServerError()
                .body(Map.of(
                    "error", "Failed to update brochure",
                    "message", e.getMessage()
                ));
        }
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<?> deleteBrochure(@PathVariable Long id) {
        try {
            log.info("Deleting brochure ID: {}", id);
            brochureService.deleteBrochure(id);
            return ResponseEntity.ok().build();
        } catch (Exception e) {
            log.error("Error deleting brochure: ", e);
            return ResponseEntity.internalServerError()
                .body(Map.of(
                    "error", "Failed to delete brochure",
                    "message", e.getMessage()
                ));
        }
    }
}
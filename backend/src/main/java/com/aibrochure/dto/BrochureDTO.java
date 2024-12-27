package com.aibrochure.dto;

import lombok.Data;
import java.time.LocalDateTime;
import java.util.List;

@Data
public class BrochureDTO {
    private Long id;
    private String title;
    private String description;
    private String content;
    private List<String> images;
    private String thumbnail;
    private String template;
    private String status;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
    private UserDTO user;
}

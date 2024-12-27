package com.aibrochure.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class BrochureRequest {
    @NotBlank(message = "Name is required")
    private String name;
    
    @NotBlank(message = "Prompt is required")
    private String prompt;
    
    private String layout = "full_bleed";  // default value
}

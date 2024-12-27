package com.aibrochure.dto;

import lombok.Data;
import java.util.List;

@Data
public class BrochureResponse {
    private String content;
    private List<String> images;
    private String template;
    private String error;
}

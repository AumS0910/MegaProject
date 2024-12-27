package com.aibrochure.service.ai;

import lombok.Data;
import org.springframework.stereotype.Service;
import java.util.ArrayList;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

@Service
public class PromptProcessingService {

    @Data
    public static class ProcessedPrompt {
        private List<String> imagePrompts;
        private String textPrompt;
    }

    public ProcessedPrompt processPrompt(String prompt) {
        ProcessedPrompt result = new ProcessedPrompt();
        
        // Extract visual elements using keywords and patterns
        List<String> visualElements = extractVisualElements(prompt);
        result.setImagePrompts(visualElements);
        
        // Clean and format the text prompt
        String textPrompt = cleanTextPrompt(prompt);
        result.setTextPrompt(textPrompt);
        
        return result;
    }

    private List<String> extractVisualElements(String prompt) {
        List<String> visualElements = new ArrayList<>();
        
        // Common visual indicators
        String[] visualKeywords = {"showing", "featuring", "with", "including", "displaying"};
        
        // Extract phrases after visual keywords
        for (String keyword : visualKeywords) {
            Pattern pattern = Pattern.compile(keyword + "\\s+([^,.]+)");
            Matcher matcher = pattern.matcher(prompt.toLowerCase());
            
            while (matcher.find()) {
                String element = matcher.group(1).trim();
                if (!visualElements.contains(element)) {
                    visualElements.add(element);
                }
            }
        }
        
        // If no visual elements found, use the whole prompt
        if (visualElements.isEmpty()) {
            visualElements.add(prompt);
        }
        
        return visualElements;
    }

    private String cleanTextPrompt(String prompt) {
        // Remove specific image-related phrases
        String cleaned = prompt;
        for (String keyword : new String[]{"show", "display", "include", "featuring"}) {
            cleaned = cleaned.replaceAll("(?i)" + keyword + "\\s+[^,.]+", "");
        }
        
        // Add tourism-specific context
        cleaned = "Create engaging travel content for: " + cleaned;
        
        return cleaned.trim();
    }
}

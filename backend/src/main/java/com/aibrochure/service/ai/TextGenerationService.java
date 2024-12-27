package com.aibrochure.service.ai;

import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.Map;

@Service
@RequiredArgsConstructor
public class TextGenerationService {

    @Value("${ai.t5.url:http://127.0.0.1:8005}")
    private String t5ServerUrl;

    private final RestTemplate restTemplate;

    public String generateText(String prompt) {
        try {
            var request = Map.of(
                "prompt", prompt,
                "max_length", 100
            );

            ResponseEntity<Map> response = restTemplate.postForEntity(
                t5ServerUrl + "/generate",
                request,
                Map.class
            );

            if (response.getBody() != null && response.getBody().containsKey("generated_text")) {
                return (String) response.getBody().get("generated_text");
            }

            return "Failed to generate text";
        } catch (Exception e) {
            return "Error generating text: " + e.getMessage();
        }
    }
}

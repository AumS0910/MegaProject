package com.aibrochure.service.ai;

import com.aibrochure.config.AIModelConfig;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.HashMap;
import java.util.Map;

@Service
@Slf4j
@RequiredArgsConstructor
public class FlanT5TextService {
    private final AIModelConfig aiModelConfig;
    private final RestTemplate restTemplate;

    // Update this path to your local model path
    private static final String MODEL_PATH = "D:/AI-Models/flan-t5/";

    public String generateText(String prompt) {
        try {
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);

            Map<String, Object> requestBody = new HashMap<>();
            requestBody.put("prompt", prompt);
            requestBody.put("max_length", 500);
            requestBody.put("temperature", 0.7);
            requestBody.put("top_p", 0.9);
            requestBody.put("model_path", MODEL_PATH);
            requestBody.put("use_local_model", true);

            HttpEntity<Map<String, Object>> request = new HttpEntity<>(requestBody, headers);

            // Update to your local model endpoint
            String localEndpoint = "http://localhost:7861/generate";
            
            Map<String, String> response = restTemplate.postForObject(
                localEndpoint,
                request,
                Map.class
            );

            return response.get("generated_text");
        } catch (Exception e) {
            log.error("Error generating text with local Flan-T5 model", e);
            throw new RuntimeException("Failed to generate text: " + e.getMessage());
        }
    }
}

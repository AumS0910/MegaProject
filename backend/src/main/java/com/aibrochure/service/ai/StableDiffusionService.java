package com.aibrochure.service.ai;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Base64;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
@Slf4j
@RequiredArgsConstructor
public class StableDiffusionService {
    private final RestTemplate restTemplate;

    // Update this to match your Kohya model filename in Stable Diffusion
    private static final String MODEL_NAME = "kohya_model.safetensors";
    private static final String API_URL = "http://127.0.0.1:7860/sdapi/v1/txt2img";

    public String generateImage(String prompt) {
        try {
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);

            Map<String, Object> requestBody = new HashMap<>();
            requestBody.put("prompt", prompt);
            requestBody.put("negative_prompt", "low quality, blurry, distorted");
            requestBody.put("steps", 30);
            requestBody.put("cfg_scale", 7.5);
            requestBody.put("width", 1024);
            requestBody.put("height", 768);
            requestBody.put("sampler_name", "DPM++ 2M Karras");
            
            // Set the model checkpoint
            Map<String, String> overrideSettings = new HashMap<>();
            overrideSettings.put("sd_model_checkpoint", MODEL_NAME);
            requestBody.put("override_settings", overrideSettings);
            requestBody.put("override_settings_restore_afterwards", true);

            HttpEntity<Map<String, Object>> request = new HttpEntity<>(requestBody, headers);

            Map<String, Object> response = restTemplate.postForObject(
                API_URL,
                request,
                Map.class
            );

            // Extract the base64 image from response
            List<String> images = (List<String>) response.get("images");
            String base64Image = images.get(0);

            // Save the image
            byte[] imageBytes = Base64.getDecoder().decode(base64Image);
            String fileName = System.currentTimeMillis() + ".png";
            Path outputPath = Paths.get("./uploads/generated/", fileName);
            java.nio.file.Files.createDirectories(outputPath.getParent());
            java.nio.file.Files.write(outputPath, imageBytes);

            return outputPath.toString();
        } catch (Exception e) {
            log.error("Error generating image with Stable Diffusion", e);
            throw new RuntimeException("Failed to generate image: " + e.getMessage());
        }
    }

    public void setModel(String modelName) {
        try {
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);

            Map<String, Object> requestBody = new HashMap<>();
            requestBody.put("sd_model_checkpoint", modelName);

            HttpEntity<Map<String, Object>> request = new HttpEntity<>(requestBody, headers);

            restTemplate.postForObject(
                "http://127.0.0.1:7860/sdapi/v1/options",
                request,
                Map.class
            );
        } catch (Exception e) {
            log.error("Error setting model in Stable Diffusion", e);
            throw new RuntimeException("Failed to set model: " + e.getMessage());
        }
    }
}

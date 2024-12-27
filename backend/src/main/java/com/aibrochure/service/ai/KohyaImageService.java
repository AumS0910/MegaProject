package com.aibrochure.service.ai;

import com.aibrochure.config.AIModelConfig;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.core.io.FileSystemResource;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.multipart.MultipartFile;

import java.io.File;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Base64;
import java.util.HashMap;
import java.util.Map;

@Service
@Slf4j
@RequiredArgsConstructor
public class KohyaImageService {
    private final AIModelConfig aiModelConfig;
    private final RestTemplate restTemplate;

    // Update these paths to your local model paths
    private static final String MODEL_PATH = "D:/AI-Models/kohya/";
    private static final String VAE_PATH = "D:/AI-Models/kohya/vae/";
    
    public String generateImage(String prompt) {
        try {
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            
            Map<String, Object> requestBody = new HashMap<>();
            requestBody.put("prompt", prompt);
            requestBody.put("negative_prompt", "low quality, blurry, distorted");
            requestBody.put("width", 1024);
            requestBody.put("height", 768);
            requestBody.put("num_inference_steps", 30);
            requestBody.put("guidance_scale", 7.5);
            
            // Add local model paths
            requestBody.put("model_path", MODEL_PATH);
            requestBody.put("vae_path", VAE_PATH);
            requestBody.put("use_local_model", true);

            HttpEntity<Map<String, Object>> request = new HttpEntity<>(requestBody, headers);

            // Update to your local model endpoint (e.g., running on localhost)
            String localEndpoint = "http://localhost:7860/sdapi/v1/txt2img";
            
            Map<String, Object> response = restTemplate.postForObject(
                localEndpoint,
                request,
                Map.class
            );

            // Handle base64 image response
            String base64Image = (String) response.get("images[0]");
            
            // Save the image to a temporary file
            byte[] imageBytes = Base64.getDecoder().decode(base64Image);
            Path outputPath = Paths.get("./uploads/generated/", System.currentTimeMillis() + ".png");
            java.nio.file.Files.write(outputPath, imageBytes);
            
            return outputPath.toString();
        } catch (Exception e) {
            log.error("Error generating image with local Kohya model", e);
            throw new RuntimeException("Failed to generate image: " + e.getMessage());
        }
    }
}

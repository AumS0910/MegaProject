package com.aibrochure.service.ai;

import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.FileSystemResource;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.io.File;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.*;

@Service
@RequiredArgsConstructor
public class ImageGenerationService {

    @Value("${ai.stable-diffusion.url:http://127.0.0.1:7860}")
    private String stableDiffusionUrl;

    @Value("${app.generated-images-path:generated_images}")
    private String generatedImagesPath;

    private final RestTemplate restTemplate;

    public List<String> generateImages(List<String> prompts) {
        List<String> generatedImagePaths = new ArrayList<>();

        for (String prompt : prompts) {
            try {
                // Prepare request for Stable Diffusion
                Map<String, Object> requestBody = new HashMap<>();
                requestBody.put("prompt", prompt);
                requestBody.put("negative_prompt", "low quality, blurry, distorted");
                requestBody.put("steps", 20);
                requestBody.put("width", 768);
                requestBody.put("height", 512);

                // Make request to Stable Diffusion API
                ResponseEntity<Map> response = restTemplate.postForEntity(
                    stableDiffusionUrl + "/sdapi/v1/txt2img",
                    requestBody,
                    Map.class
                );

                if (response.getBody() != null && response.getBody().containsKey("images")) {
                    List<String> images = (List<String>) response.getBody().get("images");
                    if (!images.isEmpty()) {
                        // Save the base64 image
                        String imagePath = saveBase64Image(images.get(0));
                        generatedImagePaths.add(imagePath);
                    }
                }
            } catch (Exception e) {
                e.printStackTrace();
            }
        }

        return generatedImagePaths;
    }

    private String saveBase64Image(String base64Image) throws Exception {
        // Create directory if it doesn't exist
        Files.createDirectories(Paths.get(generatedImagesPath));

        // Generate unique filename
        String filename = UUID.randomUUID().toString() + ".png";
        Path filepath = Paths.get(generatedImagesPath, filename);

        // Decode and save image
        byte[] imageBytes = Base64.getDecoder().decode(base64Image);
        Files.write(filepath, imageBytes);

        return filepath.toString();
    }

    public ResponseEntity<FileSystemResource> getImage(String filename) {
        try {
            File file = new File(generatedImagesPath + "/" + filename);
            if (!file.exists()) {
                return ResponseEntity.notFound().build();
            }

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.IMAGE_PNG);
            
            return ResponseEntity
                .ok()
                .headers(headers)
                .body(new FileSystemResource(file));
        } catch (Exception e) {
            return ResponseEntity.internalServerError().build();
        }
    }
}

package com.aibrochure.service;

import com.aibrochure.dto.BrochureRequest;
import com.aibrochure.dto.BrochureResponse;
import com.aibrochure.entity.Brochure;
import com.aibrochure.entity.User;
import com.aibrochure.repository.BrochureRepository;
import com.aibrochure.repository.UserRepository;
import com.aibrochure.service.ai.ImageGenerationService;
import com.aibrochure.service.ai.PromptProcessingService;
import com.aibrochure.service.ai.TextGenerationService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.scheduling.annotation.Async;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.*;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ConcurrentHashMap;

@Slf4j
@Service
@RequiredArgsConstructor
public class BrochureService {

    private final ImageGenerationService imageGenerationService;
    private final TextGenerationService textGenerationService;
    private final PromptProcessingService promptProcessingService;
    private final BrochureRepository brochureRepository;
    private final UserRepository userRepository;

    // Store task status
    private final Map<String, Map<String, Object>> taskStatus = new ConcurrentHashMap<>();

    @Transactional
    public Map<String, Object> startBrochureGeneration(BrochureRequest request) {
        try {
            // Validate request
            if (request.getName() == null || request.getName().trim().isEmpty()) {
                throw new IllegalArgumentException("Brochure name is required");
            }
            if (request.getPrompt() == null || request.getPrompt().trim().isEmpty()) {
                throw new IllegalArgumentException("Prompt is required");
            }

            // Generate task ID
            String taskId = UUID.randomUUID().toString();
            
            // Initialize task status
            taskStatus.put(taskId, new HashMap<>() {{
                put("status", "processing");
                put("message", "Started brochure generation");
            }});

            // Start async generation
            generateBrochureAsync(taskId, request);

            // Return task ID
            return Map.of(
                "task_id", taskId,
                "status", "processing",
                "message", "Brochure generation started"
            );
        } catch (Exception e) {
            log.error("Error starting brochure generation: ", e);
            throw e;
        }
    }

    @Async
    @Transactional
    public void generateBrochureAsync(String taskId, BrochureRequest request) {
        try {
            log.info("Starting brochure generation for task {}", taskId);
            
            // Get current user
            Authentication auth = SecurityContextHolder.getContext().getAuthentication();
            User currentUser = userRepository.findByEmail(auth.getName())
                .orElseThrow(() -> new RuntimeException("User not found"));

            // Update status
            updateTaskStatus(taskId, "processing", "Processing prompt...");

            // Process the prompt
            log.info("Processing prompt: {}", request.getPrompt());
            var processedPrompt = promptProcessingService.processPrompt(request.getPrompt());

            // Generate text content
            updateTaskStatus(taskId, "processing", "Generating text content...");
            log.info("Generating text with prompt: {}", processedPrompt.getTextPrompt());
            String content = textGenerationService.generateText(processedPrompt.getTextPrompt());
            if (content == null || content.trim().isEmpty()) {
                throw new RuntimeException("Failed to generate text content");
            }

            // Generate images
            updateTaskStatus(taskId, "processing", "Generating images...");
            log.info("Generating images with prompts: {}", processedPrompt.getImagePrompts());
            List<String> images = imageGenerationService.generateImages(processedPrompt.getImagePrompts());
            if (images == null || images.isEmpty()) {
                throw new RuntimeException("Failed to generate images");
            }

            // Create and save brochure
            log.info("Creating brochure entity");
            Brochure brochure = new Brochure();
            brochure.setTitle(request.getName());
            brochure.setHotelName(extractHotelName(request.getPrompt()));
            brochure.setLocation(extractLocation(request.getPrompt())); // Extract and set location
            brochure.setTheme(extractTheme(request.getPrompt())); // Extract and set theme
            brochure.setContent(content);
            brochure.setImages(images);
            brochure.setUser(currentUser);
            brochure.setStatus("COMPLETED");
            brochure = brochureRepository.save(brochure);
            log.info("Saved brochure with ID: {}", brochure.getId());

            // Generate brochure using Python service
            String brochureImage = generateBrochureWithPythonService(brochure);
            brochure.setThumbnail(brochureImage);
            brochure = brochureRepository.save(brochure);
            log.info("Generated brochure image for ID: {}", brochure.getId());

            // Update status with success
            Map<String, Object> brochureData = new HashMap<>();
            brochureData.put("id", brochure.getId());
            brochureData.put("title", brochure.getTitle());
            brochureData.put("content", brochure.getContent());
            brochureData.put("images", brochure.getImages());
            brochureData.put("status", brochure.getStatus());
            
            updateTaskStatus(taskId, "completed", "Brochure generated successfully", brochureData);
            log.info("Brochure generation completed successfully for task {}", taskId);

        } catch (Exception e) {
            log.error("Error during brochure generation for task {}: ", taskId, e);
            // Update status with error
            updateTaskStatus(taskId, "failed", "Error: " + e.getMessage());
            throw e; // Re-throw to ensure transaction rollback
        }
    }

    public Map<String, Object> getTaskStatus(String taskId) {
        return taskStatus.getOrDefault(taskId, Map.of(
            "status", "not_found",
            "message", "Task not found"
        ));
    }

    private void updateTaskStatus(String taskId, String status, String message) {
        updateTaskStatus(taskId, status, message, null);
    }

    private void updateTaskStatus(String taskId, String status, String message, Object data) {
        Map<String, Object> statusUpdate = new HashMap<>();
        statusUpdate.put("status", status);
        statusUpdate.put("message", message);
        if (data != null) {
            statusUpdate.put("data", data);
        }
        taskStatus.put(taskId, statusUpdate);
    }

    // Helper method to extract hotel name from prompt
    private String extractHotelName(String prompt) {
        // First try to find text between quotes
        int startQuote = prompt.indexOf('"');
        int endQuote = prompt.indexOf('"', startQuote + 1);
        if (startQuote >= 0 && endQuote > startQuote) {
            return prompt.substring(startQuote + 1, endQuote);
        }

        // Try to find hotel name using common patterns
        String[] lines = prompt.split("[\\r\\n]+");
        for (String line : lines) {
            line = line.trim().toLowerCase();
            
            // Look for patterns like "for [hotel name]" or "for the [hotel name]"
            if (line.contains("for")) {
                int forIndex = line.indexOf("for");
                String afterFor = line.substring(forIndex + 3).trim();
                
                // If it starts with "the", skip it
                if (afterFor.startsWith("the ")) {
                    afterFor = afterFor.substring(4);
                }
                
                // Find the end of the hotel name (usually before a comma or keywords)
                int endIndex = afterFor.length();
                int commaIndex = afterFor.indexOf(',');
                if (commaIndex > 0) {
                    endIndex = commaIndex;
                }
                
                // Extract and clean up the name
                String name = afterFor.substring(0, endIndex).trim();
                if (!name.isEmpty()) {
                    // Properly capitalize each word
                    String[] words = name.split("\\s+");
                    StringBuilder properName = new StringBuilder();
                    for (String word : words) {
                        if (properName.length() > 0) properName.append(" ");
                        properName.append(Character.toUpperCase(word.charAt(0)))
                                .append(word.substring(1));
                    }
                    return "The " + properName.toString();
                }
            }
            
            // Fallback: look for resort/hotel keywords
            if (line.contains("resort") || line.contains("hotel")) {
                String[] words = line.split("(?i)(resort|hotel)");
                if (words.length > 0) {
                    String name = words[0].trim();
                    if (!name.isEmpty()) {
                        // Remove "the" from the beginning if present
                        if (name.toLowerCase().startsWith("the ")) {
                            name = name.substring(4);
                        }
                        return "The " + name.substring(0, 1).toUpperCase() + name.substring(1) + " Resort";
                    }
                }
            }
        }

        // If no hotel name found in the prompt, use the brochure name
        return "The Paradise Beach Resort"; // Default name
    }

    // Helper method to extract location from prompt
    private String extractLocation(String prompt) {
        // First try to find location after "in" or "at"
        String[] words = prompt.split("\\s+");
        for (int i = 0; i < words.length - 1; i++) {
            if (words[i].equalsIgnoreCase("in") || words[i].equalsIgnoreCase("at")) {
                String location = words[i + 1];
                // Remove any punctuation
                location = location.replaceAll("[.,]", "");
                if (!location.isEmpty()) {
                    return location;
                }
            }
        }

        // If no location found, try to find any known location names
        String[] commonLocations = {"Maldives", "Bali", "Hawaii", "Fiji", "Seychelles"};
        for (String location : commonLocations) {
            if (prompt.contains(location)) {
                return location;
            }
        }

        // Default location if none found
        return "Paradise Island";
    }

    // Helper method to extract theme from prompt
    private String extractTheme(String prompt) {
        // Look for common luxury/resort themes
        String[] luxuryThemes = {"Luxury", "Beach", "Resort", "Spa", "Wellness", "Adventure"};
        for (String theme : luxuryThemes) {
            if (prompt.toLowerCase().contains(theme.toLowerCase())) {
                return theme;
            }
        }
        // Default theme
        return "Luxury";
    }

    // Helper method to generate brochure using Python service
    private String generateBrochureWithPythonService(Brochure brochure) {
        try {
            // Create a process builder for the Python script
            ProcessBuilder processBuilder = new ProcessBuilder(
                "python",
                "-m",
                "models.generate_single_page_brochure",
                "--hotel_name", brochure.getHotelName(),
                "--location", brochure.getLocation(),
                "--layout", "full_bleed"  // Use full bleed layout
            );
            
            // Set working directory to project root
            processBuilder.directory(new java.io.File(System.getProperty("user.dir")).getParentFile());
            
            processBuilder.redirectErrorStream(true);
            Process process = processBuilder.start();
            
            // Read the output
            try (java.io.BufferedReader reader = new java.io.BufferedReader(
                    new java.io.InputStreamReader(process.getInputStream()))) {
                String line;
                while ((line = reader.readLine()) != null) {
                    log.info("Python script output: {}", line);
                }
            }
            
            int exitCode = process.waitFor();
            if (exitCode != 0) {
                throw new RuntimeException("Failed to generate brochure image. Exit code: " + exitCode);
            }
            
            // Return the expected brochure path
            String brochureFilename = brochure.getHotelName().replaceAll("\\s+", "_") + "_full_bleed_brochure.png";
            return "generated_brochures/" + brochureFilename;
        } catch (Exception e) {
            log.error("Error generating brochure image: ", e);
            throw new RuntimeException("Failed to generate brochure image", e);
        }
    }

    // Helper method to generate brochure HTML
    private String generateBrochureHtml(Brochure brochure) {
        StringBuilder html = new StringBuilder();
        html.append("<!DOCTYPE html>\n")
            .append("<html lang=\"en\">\n")
            .append("<head>\n")
            .append("    <meta charset=\"UTF-8\">\n")
            .append("    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n")
            .append("    <title>").append(brochure.getTitle()).append("</title>\n")
            .append("    <style>\n")
            .append("        body { font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; }\n")
            .append("        .container { max-width: 1200px; margin: 0 auto; }\n")
            .append("        .header { text-align: center; margin-bottom: 40px; }\n")
            .append("        .content { margin-bottom: 40px; }\n")
            .append("        .image-gallery { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }\n")
            .append("        .image-gallery img { width: 100%; height: auto; border-radius: 8px; }\n")
            .append("    </style>\n")
            .append("</head>\n")
            .append("<body>\n")
            .append("    <div class=\"container\">\n")
            .append("        <div class=\"header\">\n")
            .append("            <h1>").append(brochure.getTitle()).append("</h1>\n")
            .append("            <h2>").append(brochure.getHotelName()).append(" - ").append(brochure.getLocation()).append("</h2>\n")
            .append("        </div>\n")
            .append("        <div class=\"content\">\n")
            .append("            ").append(brochure.getContent().replace("\n", "<br>")).append("\n")
            .append("        </div>\n")
            .append("        <div class=\"image-gallery\">\n");
        
        for (String image : brochure.getImages()) {
            html.append("            <img src=\"../").append(image).append("\" alt=\"Hotel Image\">\n");
        }
        
        html.append("        </div>\n")
            .append("    </div>\n")
            .append("</body>\n")
            .append("</html>");

        return html.toString();
    }

    // Helper method to save brochure HTML to file
    private void saveBrochureToFile(Long brochureId, String html) {
        try {
            java.nio.file.Path brochuresDir = java.nio.file.Paths.get("generated_brochures");
            if (!java.nio.file.Files.exists(brochuresDir)) {
                java.nio.file.Files.createDirectories(brochuresDir);
            }
            
            java.nio.file.Path brochureFile = brochuresDir.resolve(brochureId + ".html");
            java.nio.file.Files.writeString(brochureFile, html);
        } catch (Exception e) {
            log.error("Error saving brochure file: ", e);
            throw new RuntimeException("Failed to save brochure file", e);
        }
    }

    // Existing methods for CRUD operations
    @Transactional(readOnly = true)
    public Page<Brochure> getAllBrochures(String search, Pageable pageable) {
        if (search != null && !search.isEmpty()) {
            return brochureRepository.findByTitleContainingIgnoreCase(search, pageable);
        }
        return brochureRepository.findAll(pageable);
    }

    @Transactional(readOnly = true)
    public Optional<Brochure> getBrochureById(Long id) {
        return brochureRepository.findById(id);
    }

    @Transactional
    public Brochure createBrochure(Brochure brochure) {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        User currentUser = userRepository.findByEmail(auth.getName())
            .orElseThrow(() -> new RuntimeException("User not found"));
        brochure.setUser(currentUser);
        return brochureRepository.save(brochure);
    }

    @Transactional
    public Brochure updateBrochure(Long id, Brochure brochure) {
        if (!brochureRepository.existsById(id)) {
            throw new RuntimeException("Brochure not found with id: " + id);
        }
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        User currentUser = userRepository.findByEmail(auth.getName())
            .orElseThrow(() -> new RuntimeException("User not found"));
        brochure.setId(id);
        brochure.setUser(currentUser);
        return brochureRepository.save(brochure);
    }

    @Transactional
    public void deleteBrochure(Long id) {
        brochureRepository.deleteById(id);
    }
}
package com.aibrochure.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;
import lombok.Data;

@Configuration
@ConfigurationProperties(prefix = "stable-diffusion")
@Data
public class StableDiffusionConfig {
    private String apiUrl = "http://127.0.0.1:7860";
    private String modelName = "kohya_model.safetensors"; // Update this to your model name
    private int width = 1024;
    private int height = 768;
    private int steps = 30;
    private double cfgScale = 7.5;
    private String samplerName = "DPM++ 2M Karras";
    private String negativePrompt = "low quality, blurry, distorted";
}

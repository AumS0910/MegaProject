package com.aibrochure.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

@Configuration
@ConfigurationProperties(prefix = "ai.model")
@Data
public class AIModelConfig {
    private KohyaConfig kohya = new KohyaConfig();
    private FlanT5Config flant5 = new FlanT5Config();

    @Data
    public static class KohyaConfig {
        private String endpoint;
        private String apiKey;
        private int maxRetries = 3;
        private long timeout = 30000; // 30 seconds
    }

    @Data
    public static class FlanT5Config {
        private String endpoint;
        private String apiKey;
        private int maxRetries = 3;
        private long timeout = 15000; // 15 seconds
    }
}

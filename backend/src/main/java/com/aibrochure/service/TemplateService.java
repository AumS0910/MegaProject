package com.aibrochure.service;

import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.Map;

@Service
@RequiredArgsConstructor
public class TemplateService {
    private final Map<String, String> templates = new HashMap<>();

    {
        // Initialize default templates
        templates.put("default", """
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    .brochure {
                        max-width: 1200px;
                        margin: 0 auto;
                        font-family: Arial, sans-serif;
                    }
                    .header {
                        text-align: center;
                        padding: 20px;
                    }
                    .content {
                        display: grid;
                        grid-template-columns: 1fr 1fr;
                        gap: 20px;
                        padding: 20px;
                    }
                    .image-section img {
                        width: 100%;
                        height: auto;
                        border-radius: 8px;
                    }
                    .text-section {
                        padding: 20px;
                        background: #f9f9f9;
                        border-radius: 8px;
                    }
                </style>
            </head>
            <body>
                <div class="brochure">
                    <div class="header">
                        <h1>{{title}}</h1>
                    </div>
                    <div class="content">
                        <div class="image-section">
                            {{#images}}
                            <img src="{{.}}" alt="Brochure Image">
                            {{/images}}
                        </div>
                        <div class="text-section">
                            {{content}}
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """);

        templates.put("modern", """
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    .brochure {
                        max-width: 1200px;
                        margin: 0 auto;
                        font-family: 'Helvetica Neue', sans-serif;
                        background: #fff;
                    }
                    .header {
                        background: linear-gradient(45deg, #2196F3, #1976D2);
                        color: white;
                        padding: 40px;
                        text-align: center;
                    }
                    .content {
                        display: flex;
                        flex-wrap: wrap;
                        padding: 40px;
                        gap: 30px;
                    }
                    .image-section {
                        flex: 1;
                        min-width: 300px;
                    }
                    .image-section img {
                        width: 100%;
                        height: auto;
                        border-radius: 12px;
                        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                    }
                    .text-section {
                        flex: 1;
                        min-width: 300px;
                        padding: 30px;
                        background: #f8f9fa;
                        border-radius: 12px;
                        line-height: 1.6;
                    }
                </style>
            </head>
            <body>
                <div class="brochure">
                    <div class="header">
                        <h1>{{title}}</h1>
                    </div>
                    <div class="content">
                        <div class="image-section">
                            {{#images}}
                            <img src="{{.}}" alt="Brochure Image">
                            {{/images}}
                        </div>
                        <div class="text-section">
                            {{content}}
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """);
    }

    public String getTemplate(String templateName) {
        return templates.getOrDefault(templateName, templates.get("default"));
    }

    public String applyTemplate(String templateName, Map<String, Object> data) {
        String template = getTemplate(templateName);
        
        // Simple template variable replacement
        for (Map.Entry<String, Object> entry : data.entrySet()) {
            String key = entry.getKey();
            Object value = entry.getValue();
            
            if (value instanceof Iterable) {
                // Handle arrays/lists
                StringBuilder replacement = new StringBuilder();
                for (Object item : (Iterable<?>) value) {
                    String section = template.substring(
                        template.indexOf("{{#" + key + "}}") + key.length() + 4,
                        template.indexOf("{{/" + key + "}}")
                    );
                    replacement.append(section.replace("{{.}}", item.toString()));
                }
                template = template.replaceAll("\\{\\{#" + key + "\\}\\}.*\\{\\{/" + key + "\\}\\}", replacement.toString());
            } else {
                // Handle simple variables
                template = template.replace("{{" + key + "}}", value.toString());
            }
        }
        
        return template;
    }
}

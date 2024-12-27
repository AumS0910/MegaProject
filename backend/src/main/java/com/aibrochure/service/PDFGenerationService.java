package com.aibrochure.service;

import com.itextpdf.html2pdf.HtmlConverter;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.io.ByteArrayOutputStream;
import java.io.IOException;

@Service
@Slf4j
public class PDFGenerationService {

    public byte[] generatePDFFromHTML(String html) {
        try (ByteArrayOutputStream outputStream = new ByteArrayOutputStream()) {
            HtmlConverter.convertToPdf(html, outputStream);
            return outputStream.toByteArray();
        } catch (IOException e) {
            log.error("Error generating PDF from HTML", e);
            throw new RuntimeException("Failed to generate PDF: " + e.getMessage());
        }
    }
}

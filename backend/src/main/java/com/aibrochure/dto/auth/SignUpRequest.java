package com.aibrochure.dto.auth;

import lombok.Data;

import jakarta.validation.constraints.*;

@Data
public class SignUpRequest {
    @NotBlank
    @Size(min = 3, max = 50)
    private String name;

    @NotBlank
    @Size(max = 100)
    @Email
    private String email;

    @NotBlank
    @Size(min = 6, max = 20)
    private String password;

    private String company;
    private String role;
}

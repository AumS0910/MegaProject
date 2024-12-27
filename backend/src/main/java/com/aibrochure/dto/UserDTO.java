package com.aibrochure.dto;

import lombok.Data;

@Data
public class UserDTO {
    private Long id;
    private String name;
    private String email;
    private String company;
    private String role;
    private String avatar;
}

package com.smartparking.platform.controller.api;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import javax.sql.DataSource;
import java.sql.Connection;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/api/health")
public class HealthApiController {

    @Autowired(required = false)
    private DataSource dataSource;

    @GetMapping
    public ResponseEntity<Map<String, Object>> healthCheck() {
        Map<String, Object> response = new HashMap<>();
        response.put("status", "UP");
        response.put("platform", "Smart Parking Availability Platform");
        response.put("version", "1.0.0 (Java 21 / Spring Boot 3.3)");
        response.put("timestamp", LocalDateTime.now());

        // Test Database Connectivity
        boolean dbConnected = false;
        String dbDetails = "Unavailable";
        if (dataSource != null) {
            try (Connection conn = dataSource.getConnection()) {
                dbConnected = !conn.isClosed();
                dbDetails = conn.getMetaData().getDatabaseProductName() + " " + conn.getMetaData().getDatabaseProductVersion();
            } catch (Exception e) {
                dbDetails = "Error: " + e.getMessage();
            }
        }
        response.put("databaseConnected", dbConnected);
        response.put("databaseDetails", dbDetails);

        return ResponseEntity.ok(response);
    }
}

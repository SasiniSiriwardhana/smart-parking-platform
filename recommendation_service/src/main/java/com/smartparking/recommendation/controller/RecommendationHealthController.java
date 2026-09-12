package com.smartparking.recommendation.controller;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.Map;

/**
 * Health check controller for the Recommendation Service.
 * 
 * Contract:
 *   GET /api/recommendation/health
 *   Response 200 OK:
 *   {
 *       "status": "ok",
 *       "service": "recommendation-service"
 *   }
 */
@RestController
@RequestMapping("/api/recommendation")
public class RecommendationHealthController {

    @GetMapping("/health")
    public ResponseEntity<Map<String, String>> healthCheck() {
        Map<String, String> response = new LinkedHashMap<>();
        response.put("status", "ok");
        response.put("service", "recommendation-service");
        return ResponseEntity.ok(response);
    }
}

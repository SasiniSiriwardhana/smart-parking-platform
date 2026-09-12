package com.smartparking.recommendation;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * Main application class for the Smart Parking Recommendation Service.
 * 
 * Future Role (Day 6):
 * - Evaluates multi-factor parking recommendation scores based on distance,
 *   price, current occupancy, predicted vacancy, and walking duration.
 */
@SpringBootApplication
public class RecommendationServiceApplication {

    public static void main(String[] args) {
        SpringApplication.run(RecommendationServiceApplication.class, args);
    }
}

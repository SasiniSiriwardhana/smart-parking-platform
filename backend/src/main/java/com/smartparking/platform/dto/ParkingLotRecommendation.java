package com.smartparking.platform.dto;

import com.smartparking.platform.model.ParkingLot;
import lombok.*;

import java.math.BigDecimal;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ParkingLotRecommendation {

    private Long lotId;
    private String name;
    private String address;
    private String city;
    private Double latitude;
    private Double longitude;
    private BigDecimal hourlyRate;
    private Integer totalCapacity;
    private Long availableSpots;
    private Double occupancyRatePercentage;
    private Boolean hasEvCharging;
    private Boolean isCovered;
    private Boolean hasCctvSecurity;

    private Double distanceKm;
    private Integer estimatedWalkingMinutes;
    private Double recommendationScore; // 0.0 to 100.0
    private String matchBadge; // "Best Value", "Closest to You", "Top Rated", "High Availability"
    private String scoreRationale;
}

package com.smartparking.platform.dto;

import jakarta.validation.constraints.NotNull;
import lombok.*;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class RecommendationRequest {

    @NotNull(message = "Destination latitude is required")
    private Double destinationLatitude;

    @NotNull(message = "Destination longitude is required")
    private Double destinationLongitude;

    @Builder.Default
    private Double maxDistanceKm = 10.0;

    @Builder.Default
    private Boolean requiresEv = false;

    @Builder.Default
    private Boolean requiresCovered = false;

    /**
     * Preference modes: BALANCED, CHEAPEST, CLOSEST, HIGHEST_AVAILABILITY
     */
    @Builder.Default
    private String preference = "BALANCED";
}

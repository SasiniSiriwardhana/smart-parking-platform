package com.smartparking.platform.controller.api;

import com.smartparking.platform.dto.ParkingLotRecommendation;
import com.smartparking.platform.dto.RecommendationRequest;
import com.smartparking.platform.service.RecommendationService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/recommendations")
@RequiredArgsConstructor
public class RecommendationApiController {

    private final RecommendationService recommendationService;

    @PostMapping
    public ResponseEntity<List<ParkingLotRecommendation>> getRecommendations(
            @Valid @RequestBody RecommendationRequest request) {

        List<ParkingLotRecommendation> recommendations = recommendationService.getRecommendations(request);
        return ResponseEntity.ok(recommendations);
    }

    @GetMapping("/quick")
    public ResponseEntity<List<ParkingLotRecommendation>> getQuickRecommendations(
            @RequestParam Double lat,
            @RequestParam Double lon,
            @RequestParam(required = false, defaultValue = "BALANCED") String preference,
            @RequestParam(required = false, defaultValue = "false") Boolean ev,
            @RequestParam(required = false, defaultValue = "false") Boolean covered) {

        RecommendationRequest request = RecommendationRequest.builder()
                .destinationLatitude(lat)
                .destinationLongitude(lon)
                .preference(preference)
                .requiresEv(ev)
                .requiresCovered(covered)
                .maxDistanceKm(10.0)
                .build();

        return ResponseEntity.ok(recommendationService.getRecommendations(request));
    }
}

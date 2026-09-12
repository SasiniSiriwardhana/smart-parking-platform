package com.smartparking.platform.service;

import com.smartparking.platform.dto.ParkingLotRecommendation;
import com.smartparking.platform.dto.RecommendationRequest;
import com.smartparking.platform.model.ParkingLot;
import com.smartparking.platform.repository.ParkingLotRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

@Service
@RequiredArgsConstructor
public class RecommendationService {

    private final ParkingLotRepository parkingLotRepository;
    private static final double EARTH_RADIUS_KM = 6371.0;
    private static final double AVERAGE_WALKING_SPEED_KMH = 4.8; // ~80m per min

    public List<ParkingLotRecommendation> getRecommendations(RecommendationRequest request) {
        List<ParkingLot> allLots = parkingLotRepository.findByIsActiveTrue();
        List<ParkingLotRecommendation> candidates = new ArrayList<>();

        double userLat = request.getDestinationLatitude();
        double userLon = request.getDestinationLongitude();
        double maxDist = request.getMaxDistanceKm() != null ? request.getMaxDistanceKm() : 15.0;

        for (ParkingLot lot : allLots) {
            // Apply amenity constraints if specified
            if (Boolean.TRUE.equals(request.getRequiresEv()) && !Boolean.TRUE.equals(lot.getHasEvCharging())) {
                continue;
            }
            if (Boolean.TRUE.equals(request.getRequiresCovered()) && !Boolean.TRUE.equals(lot.getIsCovered())) {
                continue;
            }

            double distance = calculateDistanceKm(userLat, userLon, lot.getLatitude(), lot.getLongitude());
            if (distance > maxDist) {
                continue;
            }

            long availableSpots = lot.getAvailableSpotsCount();
            double occupancyPct = lot.getOccupancyRate();
            int walkingMinutes = (int) Math.round((distance / AVERAGE_WALKING_SPEED_KMH) * 60.0);

            ParkingLotRecommendation rec = ParkingLotRecommendation.builder()
                    .lotId(lot.getId())
                    .name(lot.getName())
                    .address(lot.getAddress())
                    .city(lot.getCity())
                    .latitude(lot.getLatitude())
                    .longitude(lot.getLongitude())
                    .hourlyRate(lot.getHourlyRate())
                    .totalCapacity(lot.getTotalCapacity())
                    .availableSpots(availableSpots)
                    .occupancyRatePercentage(Math.round(occupancyPct * 10.0) / 10.0)
                    .hasEvCharging(lot.getHasEvCharging())
                    .isCovered(lot.getIsCovered())
                    .hasCctvSecurity(lot.getHasCctvSecurity())
                    .distanceKm(Math.round(distance * 100.0) / 100.0)
                    .estimatedWalkingMinutes(Math.max(1, walkingMinutes))
                    .build();

            candidates.add(rec);
        }

        if (candidates.isEmpty()) {
            return candidates;
        }

        // Determine min/max for normalization
        double maxDistanceFound = candidates.stream().mapToDouble(ParkingLotRecommendation::getDistanceKm).max().orElse(1.0);
        double minPrice = candidates.stream().mapToDouble(c -> c.getHourlyRate().doubleValue()).min().orElse(1.0);
        double maxPrice = candidates.stream().mapToDouble(c -> c.getHourlyRate().doubleValue()).max().orElse(10.0);

        String preference = request.getPreference() != null ? request.getPreference().toUpperCase() : "BALANCED";

        // Weights: [Distance, Price, Vacancy, Amenities]
        double wDist = 0.40;
        double wPrice = 0.30;
        double wAvail = 0.20;
        double wAmenity = 0.10;

        switch (preference) {
            case "CHEAPEST":
                wPrice = 0.60;
                wDist = 0.20;
                wAvail = 0.15;
                wAmenity = 0.05;
                break;
            case "CLOSEST":
                wDist = 0.65;
                wPrice = 0.15;
                wAvail = 0.15;
                wAmenity = 0.05;
                break;
            case "HIGHEST_AVAILABILITY":
                wAvail = 0.55;
                wDist = 0.25;
                wPrice = 0.15;
                wAmenity = 0.05;
                break;
            default: // BALANCED
                break;
        }

        for (ParkingLotRecommendation rec : candidates) {
            // Distance score: closer -> higher (100 is best)
            double distScore = Math.max(0.0, 100.0 * (1.0 - (rec.getDistanceKm() / Math.max(maxDistanceFound, 0.1))));

            // Price score: cheaper -> higher
            double priceRange = maxPrice - minPrice;
            double priceScore = priceRange > 0
                    ? 100.0 * (1.0 - ((rec.getHourlyRate().doubleValue() - minPrice) / priceRange))
                    : 100.0;

            // Availability score: higher available spots -> higher
            double vacancyRatio = rec.getTotalCapacity() > 0 ? (double) rec.getAvailableSpots() / rec.getTotalCapacity() : 0.0;
            double availScore = Math.min(100.0, vacancyRatio * 100.0);

            // Amenity bonus
            double amenityScore = 0.0;
            if (Boolean.TRUE.equals(rec.getHasEvCharging())) amenityScore += 40.0;
            if (Boolean.TRUE.equals(rec.getIsCovered())) amenityScore += 30.0;
            if (Boolean.TRUE.equals(rec.getHasCctvSecurity())) amenityScore += 30.0;

            double finalScore = (wDist * distScore) + (wPrice * priceScore) + (wAvail * availScore) + (wAmenity * amenityScore);
            rec.setRecommendationScore(Math.round(finalScore * 10.0) / 10.0);

            // Badging logic
            if (rec.getDistanceKm() <= 0.5) {
                rec.setMatchBadge("Closest Walking Distance");
                rec.setScoreRationale("Only " + rec.getEstimatedWalkingMinutes() + " mins walk away");
            } else if (rec.getHourlyRate().doubleValue() <= minPrice) {
                rec.setMatchBadge("Best Value Rate");
                rec.setScoreRationale("Lowest hourly rate in the target area");
            } else if (rec.getAvailableSpots() >= 10) {
                rec.setMatchBadge("High Vacancy");
                rec.setScoreRationale(rec.getAvailableSpots() + " slots currently vacant");
            } else {
                rec.setMatchBadge("Recommended");
                rec.setScoreRationale("Optimal balance of distance and pricing");
            }
        }

        // Sort descending by recommendation score
        candidates.sort(Comparator.comparing(ParkingLotRecommendation::getRecommendationScore).reversed());
        return candidates;
    }

    /**
     * Haversine formula calculation for geographical coordinates.
     */
    public static double calculateDistanceKm(double lat1, double lon1, double lat2, double lon2) {
        double dLat = Math.toRadians(lat2 - lat1);
        double dLon = Math.toRadians(lon2 - lon1);
        double a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
                Math.cos(Math.toRadians(lat1)) * Math.cos(Math.toRadians(lat2)) *
                        Math.sin(dLon / 2) * Math.sin(dLon / 2);
        double c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        return EARTH_RADIUS_KM * c;
    }
}

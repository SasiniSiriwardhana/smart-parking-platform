package com.smartparking.platform.service;

import com.smartparking.platform.model.ParkingLot;
import com.smartparking.platform.model.ParkingSpot;
import com.smartparking.platform.model.SpotType;
import com.smartparking.platform.repository.ParkingLotRepository;
import com.smartparking.platform.repository.ParkingSpotRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Optional;

@Service
@RequiredArgsConstructor
public class ParkingLotService {

    private final ParkingLotRepository parkingLotRepository;
    private final ParkingSpotRepository parkingSpotRepository;

    public List<ParkingLot> getAllActiveLots() {
        return parkingLotRepository.findByIsActiveTrue();
    }

    public List<ParkingLot> searchLots(String query) {
        if (query == null || query.trim().isEmpty()) {
            return getAllActiveLots();
        }
        return parkingLotRepository.searchLots(query.trim());
    }

    public Optional<ParkingLot> getLotById(Long id) {
        return parkingLotRepository.findById(id);
    }

    public List<ParkingSpot> getSpotsForLot(Long lotId) {
        return parkingSpotRepository.findByParkingLotId(lotId);
    }

    public List<ParkingSpot> getAvailableSpots(Long lotId, SpotType spotType) {
        if (spotType != null) {
            return parkingSpotRepository.findByParkingLotIdAndSpotTypeAndIsOccupiedFalseAndIsReservedFalse(lotId, spotType);
        }
        return parkingSpotRepository.findByParkingLotIdAndIsOccupiedFalseAndIsReservedFalse(lotId);
    }

    @Transactional
    public ParkingSpot toggleSpotOccupancy(Long spotId) {
        ParkingSpot spot = parkingSpotRepository.findById(spotId)
                .orElseThrow(() -> new IllegalArgumentException("Spot not found with ID: " + spotId));
        spot.setIsOccupied(!spot.getIsOccupied());
        return parkingSpotRepository.save(spot);
    }

    @Transactional
    public ParkingLot saveLot(ParkingLot lot) {
        return parkingLotRepository.save(lot);
    }
}

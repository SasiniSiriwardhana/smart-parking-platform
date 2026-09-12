package com.smartparking.platform.repository;

import com.smartparking.platform.model.ParkingSpot;
import com.smartparking.platform.model.SpotType;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface ParkingSpotRepository extends JpaRepository<ParkingSpot, Long> {

    List<ParkingSpot> findByParkingLotId(Long parkingLotId);

    List<ParkingSpot> findByParkingLotIdAndIsOccupiedFalseAndIsReservedFalse(Long parkingLotId);

    List<ParkingSpot> findByParkingLotIdAndSpotTypeAndIsOccupiedFalseAndIsReservedFalse(Long parkingLotId, SpotType spotType);

    Optional<ParkingSpot> findFirstByParkingLotIdAndIsOccupiedFalseAndIsReservedFalse(Long parkingLotId);

    Optional<ParkingSpot> findFirstByParkingLotIdAndSpotTypeAndIsOccupiedFalseAndIsReservedFalse(Long parkingLotId, SpotType spotType);
}

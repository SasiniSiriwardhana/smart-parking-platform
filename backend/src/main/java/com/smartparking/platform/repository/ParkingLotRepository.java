package com.smartparking.platform.repository;

import com.smartparking.platform.model.ParkingLot;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface ParkingLotRepository extends JpaRepository<ParkingLot, Long> {

    List<ParkingLot> findByIsActiveTrue();

    @Query("SELECT p FROM ParkingLot p WHERE p.isActive = true AND " +
           "(LOWER(p.name) LIKE LOWER(CONCAT('%', :query, '%')) OR " +
           " LOWER(p.address) LIKE LOWER(CONCAT('%', :query, '%')) OR " +
           " LOWER(p.city) LIKE LOWER(CONCAT('%', :query, '%')))")
    List<ParkingLot> searchLots(@Param("query") String query);

    List<ParkingLot> findByIsActiveTrueAndHasEvChargingTrue();

    List<ParkingLot> findByIsActiveTrueAndIsCoveredTrue();
}

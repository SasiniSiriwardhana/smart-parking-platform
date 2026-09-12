package com.smartparking.platform.repository;

import com.smartparking.platform.model.Reservation;
import com.smartparking.platform.model.ReservationStatus;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;

@Repository
public interface ReservationRepository extends JpaRepository<Reservation, Long> {

    List<Reservation> findByUserIdOrderByCreatedAtDesc(Long userId);

    List<Reservation> findByParkingSpotIdAndStatusIn(Long parkingSpotId, List<ReservationStatus> statuses);

    @Query("SELECT r FROM Reservation r WHERE r.status = 'PENDING_HOLD' AND r.holdExpiresAt < :now")
    List<Reservation> findExpiredHolds(@Param("now") LocalDateTime now);

    List<Reservation> findByStatus(ReservationStatus status);
}

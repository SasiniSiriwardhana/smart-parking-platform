package com.smartparking.platform.repository;

import com.smartparking.platform.model.ParkingSession;
import com.smartparking.platform.model.SessionStatus;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface ParkingSessionRepository extends JpaRepository<ParkingSession, Long> {

    List<ParkingSession> findByUserIdOrderByCheckInTimeDesc(Long userId);

    Optional<ParkingSession> findFirstByUserIdAndStatus(Long userId, SessionStatus status);

    Optional<ParkingSession> findByParkingSpotIdAndStatus(Long parkingSpotId, SessionStatus status);

    List<ParkingSession> findByStatus(SessionStatus status);
}

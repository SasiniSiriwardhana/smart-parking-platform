package com.smartparking.platform.service;

import com.smartparking.platform.model.*;
import com.smartparking.platform.repository.ParkingLotRepository;
import com.smartparking.platform.repository.ParkingSpotRepository;
import com.smartparking.platform.repository.ParkingSessionRepository;
import com.smartparking.platform.repository.ReservationRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.Duration;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

@Slf4j
@Service
@RequiredArgsConstructor
public class ParkingSessionService {

    private final ParkingSessionRepository sessionRepository;
    private final ParkingSpotRepository spotRepository;
    private final ReservationRepository reservationRepository;

    @Transactional
    public ParkingSession checkIn(User user, Long reservationId, Long spotId) {
        ParkingSpot spot;
        Reservation reservation = null;

        if (reservationId != null) {
            reservation = reservationRepository.findById(reservationId)
                    .orElseThrow(() -> new IllegalArgumentException("Reservation not found: " + reservationId));
            spot = reservation.getParkingSpot();
            reservation.setStatus(ReservationStatus.ACTIVE_PARKING);
            reservationRepository.save(reservation);
        } else if (spotId != null) {
            spot = spotRepository.findById(spotId)
                    .orElseThrow(() -> new IllegalArgumentException("Spot not found: " + spotId));
            if (spot.getIsOccupied()) {
                throw new IllegalStateException("Spot is already occupied.");
            }
        } else {
            throw new IllegalArgumentException("Either reservationId or spotId must be provided for check-in.");
        }

        spot.setIsOccupied(true);
        spot.setIsReserved(false);
        spotRepository.save(spot);

        ParkingSession session = ParkingSession.builder()
                .user(user)
                .parkingSpot(spot)
                .reservation(reservation)
                .checkInTime(LocalDateTime.now())
                .status(SessionStatus.ACTIVE)
                .isPaid(false)
                .build();

        return sessionRepository.save(session);
    }

    @Transactional
    public ParkingSession checkOut(Long sessionId, User user) {
        ParkingSession session = sessionRepository.findById(sessionId)
                .orElseThrow(() -> new IllegalArgumentException("Session not found: " + sessionId));

        if (session.getStatus() != SessionStatus.ACTIVE) {
            throw new IllegalStateException("Session is already closed: " + session.getStatus());
        }

        LocalDateTime checkOutTime = LocalDateTime.now();
        session.setCheckOutTime(checkOutTime);

        long durationMinutes = Duration.between(session.getCheckInTime(), checkOutTime).toMinutes();
        if (durationMinutes < 1) durationMinutes = 1;
        session.setDurationMinutes(durationMinutes);

        // Tariff calculation: ceil to nearest hour
        long billableHours = (long) Math.ceil((double) durationMinutes / 60.0);
        BigDecimal hourlyRate = session.getParkingSpot().getParkingLot().getHourlyRate();
        BigDecimal totalAmount = hourlyRate.multiply(BigDecimal.valueOf(billableHours));

        session.setCalculatedAmount(totalAmount.setScale(2, RoundingMode.HALF_UP));
        session.setStatus(SessionStatus.COMPLETED);
        session.setIsPaid(true);

        // Free up spot
        ParkingSpot spot = session.getParkingSpot();
        spot.setIsOccupied(false);
        spot.setIsReserved(false);
        spotRepository.save(spot);

        if (session.getReservation() != null) {
            session.getReservation().setStatus(ReservationStatus.COMPLETED);
            reservationRepository.save(session.getReservation());
        }

        return sessionRepository.save(session);
    }

    public List<ParkingSession> getUserSessions(Long userId) {
        return sessionRepository.findByUserIdOrderByCheckInTimeDesc(userId);
    }

    public Optional<ParkingSession> getActiveUserSession(Long userId) {
        return sessionRepository.findFirstByUserIdAndStatus(userId, SessionStatus.ACTIVE);
    }
}

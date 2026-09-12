package com.smartparking.platform.service;

import com.smartparking.platform.dto.ReservationRequest;
import com.smartparking.platform.model.*;
import com.smartparking.platform.repository.ParkingLotRepository;
import com.smartparking.platform.repository.ParkingSpotRepository;
import com.smartparking.platform.repository.ReservationRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

@Slf4j
@Service
@RequiredArgsConstructor
public class ReservationService {

    private final ReservationRepository reservationRepository;
    private final ParkingSpotRepository parkingSpotRepository;
    private final ParkingLotRepository parkingLotRepository;

    /**
     * Holds a spot for 15 minutes to guarantee reservation before expiration.
     */
    @Transactional
    public Reservation createReservationHold(User user, ReservationRequest request) {
        ParkingLot lot = parkingLotRepository.findById(request.getParkingLotId())
                .orElseThrow(() -> new IllegalArgumentException("Parking lot not found: " + request.getParkingLotId()));

        ParkingSpot spot;
        if (request.getSpecificSpotId() != null) {
            spot = parkingSpotRepository.findById(request.getSpecificSpotId())
                    .orElseThrow(() -> new IllegalArgumentException("Spot not found: " + request.getSpecificSpotId()));
            if (spot.getIsOccupied() || spot.getIsReserved()) {
                throw new IllegalStateException("Selected spot " + spot.getSpotNumber() + " is no longer available.");
            }
        } else {
            SpotType type = request.getSpotType() != null ? request.getSpotType() : SpotType.STANDARD;
            spot = parkingSpotRepository.findFirstByParkingLotIdAndSpotTypeAndIsOccupiedFalseAndIsReservedFalse(lot.getId(), type)
                    .orElseGet(() -> parkingSpotRepository.findFirstByParkingLotIdAndIsOccupiedFalseAndIsReservedFalse(lot.getId())
                            .orElseThrow(() -> new IllegalStateException("No available spots in this parking lot.")));
        }

        // Lock spot
        spot.setIsReserved(true);
        parkingSpotRepository.save(spot);

        LocalDateTime now = LocalDateTime.now();
        int hours = request.getDurationHours() != null && request.getDurationHours() > 0 ? request.getDurationHours() : 2;
        BigDecimal totalCost = lot.getHourlyRate().multiply(BigDecimal.valueOf(hours));

        Reservation reservation = Reservation.builder()
                .user(user)
                .parkingSpot(spot)
                .startTime(now)
                .endTime(now.plusHours(hours))
                .holdExpiresAt(now.plusMinutes(15)) // 15-minute hold timer
                .status(ReservationStatus.PENDING_HOLD)
                .totalAmount(totalCost)
                .licensePlate(request.getLicensePlate() != null ? request.getLicensePlate() : user.getVehicleNumber())
                .build();

        return reservationRepository.save(reservation);
    }

    @Transactional
    public Reservation confirmReservation(Long reservationId, User user) {
        Reservation reservation = reservationRepository.findById(reservationId)
                .orElseThrow(() -> new IllegalArgumentException("Reservation not found: " + reservationId));

        if (!reservation.getUser().getId().equals(user.getId()) && !user.getRole().equals(Role.ROLE_ADMIN)) {
            throw new org.springframework.security.access.AccessDeniedException("Unauthorized to confirm this reservation.");
        }

        if (reservation.getStatus() != ReservationStatus.PENDING_HOLD) {
            throw new IllegalStateException("Reservation cannot be confirmed. Current status: " + reservation.getStatus());
        }

        if (reservation.getHoldExpiresAt() != null && reservation.getHoldExpiresAt().isBefore(LocalDateTime.now())) {
            releaseExpiredSpot(reservation);
            throw new IllegalStateException("Hold time expired. Please create a new reservation.");
        }

        reservation.setStatus(ReservationStatus.CONFIRMED);
        return reservationRepository.save(reservation);
    }

    @Transactional
    public Reservation cancelReservation(Long reservationId, User user) {
        Reservation reservation = reservationRepository.findById(reservationId)
                .orElseThrow(() -> new IllegalArgumentException("Reservation not found: " + reservationId));

        if (!reservation.getUser().getId().equals(user.getId()) && !user.getRole().equals(Role.ROLE_ADMIN)) {
            throw new org.springframework.security.access.AccessDeniedException("Unauthorized to cancel this reservation.");
        }

        releaseExpiredSpot(reservation);
        reservation.setStatus(ReservationStatus.CANCELLED);
        return reservationRepository.save(reservation);
    }

    public List<Reservation> getUserReservations(Long userId) {
        return reservationRepository.findByUserIdOrderByCreatedAtDesc(userId);
    }

    public Optional<Reservation> getReservationById(Long id) {
        return reservationRepository.findById(id);
    }

    /**
     * Periodic background cleanup for expired holds (every 60 seconds).
     */
    @Scheduled(fixedRate = 60000)
    @Transactional
    public void cleanupExpiredHolds() {
        List<Reservation> expiredList = reservationRepository.findExpiredHolds(LocalDateTime.now());
        for (Reservation res : expiredList) {
            log.info("Expiring reservation hold #{} for spot {}", res.getId(), res.getParkingSpot().getSpotNumber());
            releaseExpiredSpot(res);
            res.setStatus(ReservationStatus.EXPIRED);
            reservationRepository.save(res);
        }
    }

    private void releaseExpiredSpot(Reservation res) {
        ParkingSpot spot = res.getParkingSpot();
        if (spot != null) {
            spot.setIsReserved(false);
            parkingSpotRepository.save(spot);
        }
    }
}

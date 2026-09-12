package com.smartparking.platform.config;

import com.smartparking.platform.model.*;
import com.smartparking.platform.repository.ParkingLotRepository;
import com.smartparking.platform.repository.ParkingSpotRepository;
import com.smartparking.platform.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.CommandLineRunner;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;

@Slf4j
@Component
@RequiredArgsConstructor
public class DataInitializer implements CommandLineRunner {

    private final UserRepository userRepository;
    private final ParkingLotRepository parkingLotRepository;
    private final ParkingSpotRepository parkingSpotRepository;
    private final PasswordEncoder passwordEncoder;

    @Override
    @Transactional
    public void run(String... args) {
        if (userRepository.count() == 0) {
            log.info("Seeding initial demo users (driver, admin)...");

            userRepository.save(User.builder()
                    .username("driver")
                    .email("driver@smartparking.com")
                    .password(passwordEncoder.encode("password123"))
                    .fullName("Alex Perera")
                    .phoneNumber("+94 77 123 4567")
                    .vehicleNumber("CAB-4589")
                    .role(Role.ROLE_DRIVER)
                    .enabled(true)
                    .build());

            userRepository.save(User.builder()
                    .username("admin")
                    .email("admin@smartparking.com")
                    .password(passwordEncoder.encode("admin123"))
                    .fullName("System Administrator")
                    .phoneNumber("+94 11 234 5678")
                    .vehicleNumber("WP-ADMIN-01")
                    .role(Role.ROLE_ADMIN)
                    .enabled(true)
                    .build());
        }

        if (parkingLotRepository.count() == 0) {
            log.info("Seeding initial smart parking lots and spots...");

            // Lot 1: Central Metro Hub Garage
            ParkingLot lot1 = ParkingLot.builder()
                    .name("Central Metro Hub Garage")
                    .address("100 Galle Road, Colpetty")
                    .city("Colombo")
                    .latitude(6.9056)
                    .longitude(79.8512)
                    .totalCapacity(20)
                    .hourlyRate(new BigDecimal("150.00"))
                    .hasEvCharging(true)
                    .isCovered(true)
                    .hasCctvSecurity(true)
                    .hasHandicapAccess(true)
                    .description("Premium multi-story parking facility with fast DC EV chargers, 24/7 CCTV surveillance, and automated number plate recognition.")
                    .isActive(true)
                    .build();
            parkingLotRepository.save(lot1);
            createSpotsForLot(lot1, 20, 4, 2);

            // Lot 2: Tech City Business Plaza
            ParkingLot lot2 = ParkingLot.builder()
                    .name("Tech City Business Plaza Parking")
                    .address("45 D.R. Wijewardena Mawatha, Colombo 10")
                    .city("Colombo")
                    .latitude(6.9271)
                    .longitude(79.8612)
                    .totalCapacity(15)
                    .hourlyRate(new BigDecimal("100.00"))
                    .hasEvCharging(false)
                    .isCovered(true)
                    .hasCctvSecurity(true)
                    .hasHandicapAccess(true)
                    .description("Covered multi-level garage serving business center, within 3 minutes walk to railway station.")
                    .isActive(true)
                    .build();
            parkingLotRepository.save(lot2);
            createSpotsForLot(lot2, 15, 0, 2);

            // Lot 3: Ocean View Open Lot
            ParkingLot lot3 = ParkingLot.builder()
                    .name("Ocean View Open Lot")
                    .address("12 Marine Drive, Bambalapitiya")
                    .city("Colombo")
                    .latitude(6.8920)
                    .longitude(79.8550)
                    .totalCapacity(12)
                    .hourlyRate(new BigDecimal("80.00"))
                    .hasEvCharging(true)
                    .isCovered(false)
                    .hasCctvSecurity(true)
                    .hasHandicapAccess(false)
                    .description("Budget-friendly open-air parking with ocean views, AC charging spots, and security guards.")
                    .isActive(true)
                    .build();
            parkingLotRepository.save(lot3);
            createSpotsForLot(lot3, 12, 2, 1);

            // Lot 4: Grand Cinnamon Commercial Parking
            ParkingLot lot4 = ParkingLot.builder()
                    .name("Grand Cinnamon Commercial Complex")
                    .address("77 Sir Chittampalam A. Gardiner Mawatha")
                    .city("Colombo")
                    .latitude(6.9319)
                    .longitude(79.8475)
                    .totalCapacity(25)
                    .hourlyRate(new BigDecimal("200.00"))
                    .hasEvCharging(true)
                    .isCovered(true)
                    .hasCctvSecurity(true)
                    .hasHandicapAccess(true)
                    .description("High-end smart garage with valet options, superfast EV charging, and elevator access to shopping malls.")
                    .isActive(true)
                    .build();
            parkingLotRepository.save(lot4);
            createSpotsForLot(lot4, 25, 6, 3);

            log.info("Demo data seeding completed successfully.");
        }
    }

    private void createSpotsForLot(ParkingLot lot, int totalSpots, int evSpots, int handicapSpots) {
        List<ParkingSpot> spots = new ArrayList<>();
        for (int i = 1; i <= totalSpots; i++) {
            SpotType type = SpotType.STANDARD;
            if (i <= evSpots) {
                type = SpotType.EV_CHARGING;
            } else if (i <= evSpots + handicapSpots) {
                type = SpotType.HANDICAP;
            } else if (i % 4 == 0) {
                type = SpotType.COMPACT;
            }

            // Simulate ~30% already occupied to demonstrate real-time availability
            boolean isOccupied = (i % 3 == 0);

            ParkingSpot spot = ParkingSpot.builder()
                    .parkingLot(lot)
                    .spotNumber(String.format("L%d-%02d", (i <= 10 ? 1 : 2), i))
                    .floorLevel(i <= 10 ? "Floor 1" : "Floor 2")
                    .spotType(type)
                    .isOccupied(isOccupied)
                    .isReserved(false)
                    .sensorId("SNS-" + lot.getId() + "-" + i)
                    .build();
            spots.add(spot);
        }
        parkingSpotRepository.saveAll(spots);
    }
}

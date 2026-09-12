package com.smartparking.platform.model;

import jakarta.persistence.*;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.*;
import org.hibernate.annotations.CreationTimestamp;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

@Entity
@Table(name = "PARKING_LOTS")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ParkingLot {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @NotBlank
    @Column(nullable = false, length = 120)
    private String name;

    @NotBlank
    @Column(nullable = false, length = 255)
    private String address;

    @Column(length = 60)
    private String city;

    @NotNull
    @Column(nullable = false)
    private Double latitude;

    @NotNull
    @Column(nullable = false)
    private Double longitude;

    @NotNull
    @Column(name = "total_capacity", nullable = false)
    private Integer totalCapacity;

    @NotNull
    @Column(name = "hourly_rate", nullable = false, precision = 10, scale = 2)
    private BigDecimal hourlyRate;

    @Builder.Default
    @Column(name = "has_ev_charging", nullable = false)
    private Boolean hasEvCharging = false;

    @Builder.Default
    @Column(name = "is_covered", nullable = false)
    private Boolean isCovered = false;

    @Builder.Default
    @Column(name = "has_cctv_security", nullable = false)
    private Boolean hasCctvSecurity = true;

    @Builder.Default
    @Column(name = "has_handicap_access", nullable = false)
    private Boolean hasHandicapAccess = true;

    @Column(length = 500)
    private String description;

    @Builder.Default
    @Column(name = "is_active", nullable = false)
    private Boolean isActive = true;

    @OneToMany(mappedBy = "parkingLot", cascade = CascadeType.ALL, orphanRemoval = true, fetch = FetchType.LAZY)
    @Builder.Default
    private List<ParkingSpot> spots = new ArrayList<>();

    @CreationTimestamp
    @Column(name = "created_at", updatable = false)
    private LocalDateTime createdAt;

    // Helper calculation methods
    public long getAvailableSpotsCount() {
        if (spots == null) return 0;
        return spots.stream().filter(s -> !s.getIsOccupied() && !s.getIsReserved()).count();
    }

    public double getOccupancyRate() {
        if (totalCapacity == null || totalCapacity == 0) return 0.0;
        long occupiedOrReserved = spots != null ? spots.stream().filter(s -> s.getIsOccupied() || s.getIsReserved()).count() : 0;
        return (double) occupiedOrReserved / totalCapacity * 100.0;
    }
}

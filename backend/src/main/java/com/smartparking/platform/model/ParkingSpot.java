package com.smartparking.platform.model;

import com.fasterxml.jackson.annotation.JsonIgnore;
import jakarta.persistence.*;
import jakarta.validation.constraints.NotBlank;
import lombok.*;

@Entity
@Table(name = "PARKING_SPOTS")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ParkingSpot {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "parking_lot_id", nullable = false)
    @JsonIgnore
    private ParkingLot parkingLot;

    @NotBlank
    @Column(name = "spot_number", nullable = false, length = 20)
    private String spotNumber;

    @Column(name = "floor_level", length = 20)
    @Builder.Default
    private String floorLevel = "Floor 1";

    @Enumerated(EnumType.STRING)
    @Column(name = "spot_type", nullable = false, length = 20)
    @Builder.Default
    private SpotType spotType = SpotType.STANDARD;

    @Builder.Default
    @Column(name = "is_occupied", nullable = false)
    private Boolean isOccupied = false;

    @Builder.Default
    @Column(name = "is_reserved", nullable = false)
    private Boolean isReserved = false;

    @Column(name = "sensor_id", length = 50)
    private String sensorId;
}

package com.smartparking.platform.dto;

import com.smartparking.platform.model.SpotType;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import lombok.*;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ReservationRequest {

    @NotNull(message = "Parking lot ID is required")
    private Long parkingLotId;

    private Long specificSpotId;

    @Builder.Default
    private SpotType spotType = SpotType.STANDARD;

    @Min(value = 1, message = "Reservation must be at least 1 hour")
    @Builder.Default
    private Integer durationHours = 2;

    private String licensePlate;
}

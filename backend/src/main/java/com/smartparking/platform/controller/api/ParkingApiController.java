package com.smartparking.platform.controller.api;

import com.smartparking.platform.model.ParkingLot;
import com.smartparking.platform.model.ParkingSpot;
import com.smartparking.platform.model.SpotType;
import com.smartparking.platform.service.ParkingLotService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/lots")
@RequiredArgsConstructor
public class ParkingApiController {

    private final ParkingLotService parkingLotService;

    @GetMapping
    public ResponseEntity<List<ParkingLot>> getAllLots(@RequestParam(required = false) String search) {
        List<ParkingLot> lots = parkingLotService.searchLots(search);
        return ResponseEntity.ok(lots);
    }

    @GetMapping("/{id}")
    public ResponseEntity<ParkingLot> getLotById(@PathVariable Long id) {
        return parkingLotService.getLotById(id)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }

    @GetMapping("/{id}/spots")
    public ResponseEntity<List<ParkingSpot>> getSpotsForLot(
            @PathVariable Long id,
            @RequestParam(required = false) SpotType type,
            @RequestParam(required = false, defaultValue = "false") boolean availableOnly) {

        if (availableOnly) {
            return ResponseEntity.ok(parkingLotService.getAvailableSpots(id, type));
        }
        return ResponseEntity.ok(parkingLotService.getSpotsForLot(id));
    }

    @PostMapping("/spots/{spotId}/toggle")
    public ResponseEntity<Map<String, Object>> toggleSpotOccupancy(@PathVariable Long spotId) {
        ParkingSpot updated = parkingLotService.toggleSpotOccupancy(spotId);
        Map<String, Object> resp = new HashMap<>();
        resp.put("spotId", updated.getId());
        resp.put("spotNumber", updated.getSpotNumber());
        resp.put("isOccupied", updated.getIsOccupied());
        return ResponseEntity.ok(resp);
    }
}

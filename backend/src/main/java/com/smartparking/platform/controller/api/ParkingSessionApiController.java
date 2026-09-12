package com.smartparking.platform.controller.api;

import com.smartparking.platform.model.ParkingSession;
import com.smartparking.platform.model.User;
import com.smartparking.platform.service.ParkingSessionService;
import com.smartparking.platform.service.UserService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/sessions")
@RequiredArgsConstructor
public class ParkingSessionApiController {

    private final ParkingSessionService sessionService;
    private final UserService userService;

    @PostMapping("/check-in")
    public ResponseEntity<?> checkIn(
            @AuthenticationPrincipal UserDetails userDetails,
            @RequestBody Map<String, Long> payload) {

        User user = userService.findByUsername(userDetails.getUsername())
                .orElseThrow(() -> new IllegalArgumentException("User not found"));

        Long reservationId = payload.get("reservationId");
        Long spotId = payload.get("spotId");

        try {
            ParkingSession session = sessionService.checkIn(user, reservationId, spotId);
            return ResponseEntity.ok(session);
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(e.getMessage());
        }
    }

    @PostMapping("/{sessionId}/check-out")
    public ResponseEntity<?> checkOut(
            @AuthenticationPrincipal UserDetails userDetails,
            @PathVariable Long sessionId) {

        User user = userService.findByUsername(userDetails.getUsername())
                .orElseThrow(() -> new IllegalArgumentException("User not found"));

        try {
            ParkingSession session = sessionService.checkOut(sessionId, user);
            return ResponseEntity.ok(session);
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(e.getMessage());
        }
    }

    @GetMapping("/active")
    public ResponseEntity<?> getActiveSession(@AuthenticationPrincipal UserDetails userDetails) {
        User user = userService.findByUsername(userDetails.getUsername())
                .orElseThrow(() -> new IllegalArgumentException("User not found"));

        return sessionService.getActiveUserSession(user.getId())
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.noContent().build());
    }

    @GetMapping("/my")
    public ResponseEntity<List<ParkingSession>> getMySessions(@AuthenticationPrincipal UserDetails userDetails) {
        User user = userService.findByUsername(userDetails.getUsername())
                .orElseThrow(() -> new IllegalArgumentException("User not found"));

        return ResponseEntity.ok(sessionService.getUserSessions(user.getId()));
    }
}

package com.smartparking.platform.controller.web;

import com.smartparking.platform.dto.RecommendationRequest;
import com.smartparking.platform.dto.ReservationRequest;
import com.smartparking.platform.model.ParkingLot;
import com.smartparking.platform.model.ParkingSpot;
import com.smartparking.platform.model.ParkingSession;
import com.smartparking.platform.model.Reservation;
import com.smartparking.platform.model.User;
import com.smartparking.platform.service.*;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.mvc.support.RedirectAttributes;

import java.util.List;

@Controller
@RequiredArgsConstructor
public class WebController {

    private final ParkingLotService parkingLotService;
    private final ReservationService reservationService;
    private final ParkingSessionService sessionService;
    private final RecommendationService recommendationService;
    private final UserService userService;

    @GetMapping({"/", "/home"})
    public String home(Model model) {
        List<ParkingLot> lots = parkingLotService.getAllActiveLots();
        long totalCapacity = lots.stream().mapToLong(ParkingLot::getTotalCapacity).sum();
        long availableSpots = lots.stream().mapToLong(ParkingLot::getAvailableSpotsCount).sum();

        model.addAttribute("lots", lots);
        model.addAttribute("totalCapacity", totalCapacity);
        model.addAttribute("availableSpots", availableSpots);
        model.addAttribute("occupiedSpots", totalCapacity - availableSpots);
        model.addAttribute("occupancyRate", totalCapacity > 0 ? (double)(totalCapacity - availableSpots) / totalCapacity * 100 : 0);
        return "home";
    }

    @GetMapping("/lots")
    public String lotsList(@RequestParam(required = false) String search, Model model) {
        List<ParkingLot> lots = parkingLotService.searchLots(search);
        model.addAttribute("lots", lots);
        model.addAttribute("searchQuery", search);
        return "lots";
    }

    @GetMapping("/lots/{id}")
    public String lotDetails(@PathVariable Long id, Model model) {
        ParkingLot lot = parkingLotService.getLotById(id)
                .orElseThrow(() -> new IllegalArgumentException("Lot not found: " + id));

        List<ParkingSpot> spots = parkingLotService.getSpotsForLot(id);
        model.addAttribute("lot", lot);
        model.addAttribute("spots", spots);
        model.addAttribute("reservationRequest", new ReservationRequest());
        return "lot-details";
    }

    @PostMapping("/reserve")
    public String handleReserve(
            @AuthenticationPrincipal UserDetails userDetails,
            @ModelAttribute ReservationRequest request,
            RedirectAttributes redirectAttributes) {

        if (userDetails == null) {
            return "redirect:/login";
        }

        User user = userService.findByUsername(userDetails.getUsername())
                .orElseThrow(() -> new IllegalArgumentException("User not found"));

        try {
            Reservation reservation = reservationService.createReservationHold(user, request);
            redirectAttributes.addFlashAttribute("successMessage",
                    "Spot held successfully for 15 minutes! Please confirm your reservation.");
            return "redirect:/reservations";
        } catch (Exception e) {
            redirectAttributes.addFlashAttribute("errorMessage", e.getMessage());
            return "redirect:/lots/" + request.getParkingLotId();
        }
    }

    @GetMapping("/reservations")
    public String userReservations(@AuthenticationPrincipal UserDetails userDetails, Model model) {
        if (userDetails == null) {
            return "redirect:/login";
        }

        User user = userService.findByUsername(userDetails.getUsername())
                .orElseThrow(() -> new IllegalArgumentException("User not found"));

        List<Reservation> reservations = reservationService.getUserReservations(user.getId());
        model.addAttribute("reservations", reservations);
        model.addAttribute("currentUser", user);
        return "reservations";
    }

    @PostMapping("/reservations/{id}/confirm")
    public String confirmReservation(
            @AuthenticationPrincipal UserDetails userDetails,
            @PathVariable Long id,
            RedirectAttributes redirectAttributes) {

        User user = userService.findByUsername(userDetails.getUsername())
                .orElseThrow(() -> new IllegalArgumentException("User not found"));

        try {
            reservationService.confirmReservation(id, user);
            redirectAttributes.addFlashAttribute("successMessage", "Reservation confirmed successfully!");
        } catch (Exception e) {
            redirectAttributes.addFlashAttribute("errorMessage", e.getMessage());
        }
        return "redirect:/reservations";
    }

    @PostMapping("/reservations/{id}/cancel")
    public String cancelReservation(
            @AuthenticationPrincipal UserDetails userDetails,
            @PathVariable Long id,
            RedirectAttributes redirectAttributes) {

        User user = userService.findByUsername(userDetails.getUsername())
                .orElseThrow(() -> new IllegalArgumentException("User not found"));

        try {
            reservationService.cancelReservation(id, user);
            redirectAttributes.addFlashAttribute("successMessage", "Reservation cancelled.");
        } catch (Exception e) {
            redirectAttributes.addFlashAttribute("errorMessage", e.getMessage());
        }
        return "redirect:/reservations";
    }

    @GetMapping("/recommendations")
    public String recommendationsPage(
            @RequestParam(required = false, defaultValue = "6.9271") Double lat,
            @RequestParam(required = false, defaultValue = "79.8612") Double lon,
            @RequestParam(required = false, defaultValue = "BALANCED") String preference,
            @RequestParam(required = false, defaultValue = "false") Boolean ev,
            @RequestParam(required = false, defaultValue = "false") Boolean covered,
            Model model) {

        RecommendationRequest req = RecommendationRequest.builder()
                .destinationLatitude(lat)
                .destinationLongitude(lon)
                .preference(preference)
                .requiresEv(ev)
                .requiresCovered(covered)
                .build();

        model.addAttribute("recommendationRequest", req);
        model.addAttribute("recommendations", recommendationService.getRecommendations(req));
        return "recommendations";
    }

    @GetMapping("/sessions")
    public String sessionsPage(@AuthenticationPrincipal UserDetails userDetails, Model model) {
        if (userDetails == null) {
            return "redirect:/login";
        }

        User user = userService.findByUsername(userDetails.getUsername())
                .orElseThrow(() -> new IllegalArgumentException("User not found"));

        model.addAttribute("activeSession", sessionService.getActiveUserSession(user.getId()).orElse(null));
        model.addAttribute("sessions", sessionService.getUserSessions(user.getId()));
        return "sessions";
    }

    @PostMapping("/sessions/start")
    public String startSession(
            @AuthenticationPrincipal UserDetails userDetails,
            @RequestParam(required = false) Long reservationId,
            @RequestParam(required = false) Long spotId,
            RedirectAttributes redirectAttributes) {

        User user = userService.findByUsername(userDetails.getUsername())
                .orElseThrow(() -> new IllegalArgumentException("User not found"));

        try {
            sessionService.checkIn(user, reservationId, spotId);
            redirectAttributes.addFlashAttribute("successMessage", "Parking session started! Timer is active.");
        } catch (Exception e) {
            redirectAttributes.addFlashAttribute("errorMessage", e.getMessage());
        }
        return "redirect:/sessions";
    }

    @PostMapping("/sessions/{id}/stop")
    public String stopSession(
            @AuthenticationPrincipal UserDetails userDetails,
            @PathVariable Long id,
            RedirectAttributes redirectAttributes) {

        User user = userService.findByUsername(userDetails.getUsername())
                .orElseThrow(() -> new IllegalArgumentException("User not found"));

        try {
            ParkingSession session = sessionService.checkOut(id, user);
            redirectAttributes.addFlashAttribute("successMessage",
                    "Session ended! Total fee: LKR " + session.getCalculatedAmount() + " (Duration: " + session.getDurationMinutes() + " mins)");
        } catch (Exception e) {
            redirectAttributes.addFlashAttribute("errorMessage", e.getMessage());
        }
        return "redirect:/sessions";
    }
}

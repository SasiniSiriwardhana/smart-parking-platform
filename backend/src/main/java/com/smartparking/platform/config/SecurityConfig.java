package com.smartparking.platform.config;

import lombok.RequiredArgsConstructor;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.config.annotation.authentication.configuration.AuthenticationConfiguration;
import org.springframework.security.config.annotation.method.configuration.EnableMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;

@Configuration
@EnableWebSecurity
@EnableMethodSecurity
@RequiredArgsConstructor
public class SecurityConfig {

    private final CustomUserDetailsService userDetailsService;

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    @Bean
    public AuthenticationManager authenticationManager(AuthenticationConfiguration authConfig) throws Exception {
        return authConfig.getAuthenticationManager();
    }

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
            .csrf(csrf -> csrf
                // Disable CSRF for REST APIs and H2 console
                .ignoringRequestMatchers("/api/**", "/h2-console/**")
            )
            .headers(headers -> headers.frameOptions(frameOptions -> frameOptions.sameOrigin())) // for H2 console
            .authorizeHttpRequests(auth -> auth
                // Static resources & UI pages
                .requestMatchers(
                    "/", "/home", "/lots", "/lots/**",
                    "/recommendations", "/api/recommendations/**",
                    "/api/health/**", "/api/lots/**",
                    "/login", "/register",
                    "/css/**", "/js/**", "/images/**", "/webjars/**",
                    "/h2-console/**", "/actuator/**"
                ).permitAll()
                // API Auth
                .requestMatchers("/api/auth/**").permitAll()
                // Driver Actions
                .requestMatchers("/reserve/**", "/reservations/**", "/sessions/**").authenticated()
                .requestMatchers(HttpMethod.POST, "/api/reservations/**").authenticated()
                .requestMatchers(HttpMethod.POST, "/api/sessions/**").authenticated()
                // Admin Actions
                .requestMatchers("/admin/**").hasRole("ADMIN")
                .anyRequest().authenticated()
            )
            .formLogin(form -> form
                .loginPage("/login")
                .loginProcessingUrl("/login")
                .defaultSuccessUrl("/lots", true)
                .failureUrl("/login?error=true")
                .permitAll()
            )
            .logout(logout -> logout
                .logoutUrl("/logout")
                .logoutSuccessUrl("/login?logout=true")
                .permitAll()
            );

        return http.build();
    }
}

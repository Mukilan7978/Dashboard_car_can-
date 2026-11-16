from __future__ import annotations

import math
import time

from config.settings import TANK_CAPACITY_L
from .vehicle_state import LIGHT_KEYS, TYRE_KEYS, VehicleState

GEAR_RATIOS = {1: 4.20, 2: 2.80, 3: 2.00, 4: 1.55, 5: 1.25, 6: 1.00, 7: 0.85, 8: 0.70}
GEAR_POWER = {1: 1.08, 2: 1.04, 3: 1.02, 4: 1.00, 5: 0.99, 6: 0.98, 7: 0.97, 8: 0.96}
FINAL_DRIVE = 3.20
WHEEL_RADIUS_M = 0.33
UPSHIFT = {1: 20.0, 2: 38.0, 3: 58.0, 4: 82.0, 5: 108.0, 6: 138.0, 7: 172.0}
DOWNSHIFT = {2: 14.0, 3: 30.0, 4: 48.0, 5: 72.0, 6: 98.0, 7: 126.0, 8: 158.0}
DRIVE_ACCEL = 8.0
REVERSE_ACCEL = 4.0
BRAKE_ACCEL = 12.0
EMERGENCY_ACCEL = 18.0
DRAG_K = DRIVE_ACCEL / (260.0 * 260.0)
ROLLING_RESISTANCE = 0.15
IDLE_RPM = 750.0
MAX_RPM = 8000.0


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


class VehiclePhysics:
    def step(self, state: VehicleState, dt: float) -> None:
        dt = _clamp(dt, 0.0, 0.05)
        if dt <= 0.0:
            return

        state.blink_on = (time.monotonic() % 1.0) < 0.5
        speed = state.speed_kmh
        direction = 1.0 if speed >= 0 else -1.0

        if state.gear == "P":
            speed = 0.0
            state.throttle = 0.0

        if state.gear == "D":
            self._select_automatic_gear(state, speed)

        drive = 0.0
        if state.engine_on and state.clutch < 50.0:
            if state.gear == "R":
                drive = -state.throttle * REVERSE_ACCEL
            elif state.gear in ("D", "M"):
                drive = (
                    state.throttle
                    * DRIVE_ACCEL
                    * GEAR_POWER.get(state.manual_gear, 1.0)
                )

        if state.parking_brake:
            drive = 0.0

        drag = DRAG_K * speed * abs(speed)
        rolling = ROLLING_RESISTANCE * direction if abs(speed) > 0.1 else 0.0
        brake = (state.brake * BRAKE_ACCEL)
        if state.emergency_brake:
            brake += EMERGENCY_ACCEL
        if state.parking_brake:
            brake += EMERGENCY_ACCEL
        brake *= direction

        acceleration = drive - drag - rolling - brake
        new_speed = speed + acceleration * dt

        if abs(speed) < 0.1 and drive == 0.0:
            new_speed = 0.0
        if speed >= 0.0 and new_speed < 0.0 and drive >= 0.0:
            new_speed = 0.0
        if speed <= 0.0 and new_speed > 0.0 and drive <= 0.0:
            new_speed = 0.0
        if state.gear == "P":
            new_speed = 0.0
        state.speed_kmh = _clamp(new_speed, -30.0, 260.0)

        self._update_rpm(state, dt)
        self._update_fuel_and_trip(state, dt)
        self._update_temperature_and_battery(state, dt)
        self._update_steering(state, dt)
        self._update_tyres(state, dt)
        state.last_update_monotonic = time.monotonic()

    def _select_automatic_gear(self, state: VehicleState, speed: float) -> None:
        speed = abs(speed)
        while state.manual_gear < 8 and speed >= UPSHIFT[state.manual_gear]:
            state.manual_gear += 1
        while state.manual_gear > 1 and speed <= DOWNSHIFT[state.manual_gear]:
            state.manual_gear -= 1

    def _update_rpm(self, state: VehicleState, dt: float) -> None:
        if not state.engine_on:
            target = 0.0
        elif state.gear in ("P", "N") or state.clutch > 50.0:
            target = IDLE_RPM + state.throttle * 3000.0
        else:
            ratio = GEAR_RATIOS[state.manual_gear] if state.gear in ("D", "M") else 3.5
            wheel_rpm = abs(state.speed_kmh) / 3.6 / (2.0 * math.pi * WHEEL_RADIUS_M) * 60.0
            target = wheel_rpm * FINAL_DRIVE * ratio
            if abs(state.speed_kmh) < 5.0 and state.gear in ("D", "M"):
                target += state.throttle * 2200.0
            target = _clamp(target, IDLE_RPM, MAX_RPM)
        state.rpm += (target - state.rpm) * min(1.0, dt * 7.0)
        if not state.engine_on and state.rpm < 5.0:
            state.rpm = 0.0

    def _update_fuel_and_trip(self, state: VehicleState, dt: float) -> None:
        load = 0.0
        if state.engine_on:
            load = _clamp(
                state.throttle * 0.90 + (state.rpm / MAX_RPM) * 0.35, 0.0, 1.0
            )
        state.engine_load = load * 100.0

        fuel_rate_lph = (0.55 + 12.0 * load) if state.engine_on else 0.0
        fuel_used = fuel_rate_lph / 3600.0 * dt
        state.fuel_used_l += fuel_used
        if state.fuel_percent > 0.0:
            state.fuel_percent = max(
                0.0, state.fuel_percent - fuel_used / TANK_CAPACITY_L * 100.0
            )

        speed = abs(state.speed_kmh)
        distance = speed * dt / 3600.0
        state.odometer_km += distance
        state.trip_km += distance

        if state.engine_on or speed > 0.1:
            state.trip_duration_s += dt

        state.instant_consumption = (
            fuel_rate_lph / speed * 100.0 if speed > 1.0 else 0.0
        )
        state.avg_consumption = (
            state.fuel_used_l / state.trip_km * 100.0 if state.trip_km > 0.001 else 0.0
        )
        state.avg_speed_kmh = (
            state.trip_km / (state.trip_duration_s / 3600.0)
            if state.trip_duration_s > 0.1
            else 0.0
        )

    def _update_temperature_and_battery(self, state: VehicleState, dt: float) -> None:
        if state.engine_on:
            target_temp = 92.0 + state.engine_load * 0.08
            rate = 0.25
        else:
            target_temp = state.ambient_temp_c
            rate = 0.04
        state.engine_temp_c += (target_temp - state.engine_temp_c) * min(1.0, rate * dt)

        battery_target = 14.2 if state.engine_on else 12.6
        state.battery_v += (battery_target - state.battery_v) * min(1.0, dt * 1.2)

    def _update_steering(self, state: VehicleState, dt: float) -> None:
        target = _clamp(state.steering_input, -1.0, 1.0) * 400.0
        rate = 520.0 if state.steering_setting == "SPORT" else 320.0
        delta = _clamp(target - state.steering_angle, -rate * dt, rate * dt)
        state.steering_angle += delta

    def _update_tyres(self, state: VehicleState, dt: float) -> None:
        target_temp = state.ambient_temp_c + abs(state.speed_kmh) * 0.07
        for key in TYRE_KEYS:
            state.tyre_temps_c[key] += (
                target_temp - state.tyre_temps_c[key]
            ) * min(1.0, dt * 0.05)
            state.tyre_pressures_bar[key] = state.tyre_base_bar[key] + (
                state.tyre_temps_c[key] - 20.0
            ) * 0.004

    def turn_off_unused_lights(self, state: VehicleState) -> None:
        if not state.engine_on:
            for key in LIGHT_KEYS:
                state.lights[key] = False

from __future__ import annotations

from dataclasses import dataclass, field

from config.settings import (
    BATTERY_LOW_V,
    ENGINE_HOT_C,
    FUEL_LOW_PERCENT,
    TYRE_HIGH_BAR,
    TYRE_LOW_BAR,
)

DOOR_KEYS = ("fl", "fr", "rl", "rr")
TYRE_KEYS = ("fl", "fr", "rl", "rr")
LIGHT_KEYS = ("low_beam", "high_beam", "drl", "fog")
GEAR_CODE = {"P": 0, "R": 1, "N": 2, "D": 3, "M": 4}
MODE_CODE = {"ECO": 0, "COMFORT": 1, "SPORT": 2, "SPORT PLUS": 3}
STEERING_CODE = {"COMFORT": 0, "SPORT": 1}


def _doors() -> dict[str, bool]:
    return {key: False for key in DOOR_KEYS}


def _mirrors() -> dict[str, bool]:
    return {"l": False, "r": False}


def _lights() -> dict[str, bool]:
    return {key: False for key in LIGHT_KEYS}


def _tyre_base() -> dict[str, float]:
    return {"fl": 2.40, "fr": 2.42, "rl": 2.38, "rr": 2.41}


def _tyre_temps() -> dict[str, float]:
    return {"fl": 24.0, "fr": 24.0, "rl": 24.0, "rr": 24.0}


@dataclass
class VehicleState:
    speed_kmh: float = 0.0
    rpm: float = 0.0
    engine_on: bool = False
    gear: str = "P"
    manual_gear: int = 1
    clutch: float = 0.0
    throttle: float = 0.0
    brake: float = 0.0
    emergency_brake: bool = False
    steering_input: float = 0.0
    steering_angle: float = 0.0

    fuel_percent: float = 75.0
    engine_temp_c: float = 40.0
    battery_v: float = 12.6
    odometer_km: float = 12450.0
    trip_km: float = 0.0
    trip_duration_s: float = 0.0
    fuel_used_l: float = 0.0
    avg_speed_kmh: float = 0.0
    instant_consumption: float = 0.0
    avg_consumption: float = 0.0
    engine_load: float = 0.0

    driving_mode: str = "COMFORT"
    steering_setting: str = "COMFORT"

    left_indicator: bool = False
    right_indicator: bool = False
    hazard: bool = False
    blink_on: bool = False

    lights: dict[str, bool] = field(default_factory=_lights)
    doors: dict[str, bool] = field(default_factory=_doors)
    mirrors: dict[str, bool] = field(default_factory=_mirrors)
    bonnet: bool = False
    boot: bool = False
    horn: bool = False
    seatbelt: bool = True
    parking_brake: bool = True

    ambient_temp_c: float = 22.0
    tyre_base_bar: dict[str, float] = field(default_factory=_tyre_base)
    tyre_pressures_bar: dict[str, float] = field(default_factory=_tyre_base)
    tyre_temps_c: dict[str, float] = field(default_factory=_tyre_temps)
    last_update_monotonic: float = 0.0

    @property
    def speed_abs(self) -> float:
        return abs(self.speed_kmh)

    @property
    def gear_code(self) -> int:
        return GEAR_CODE[self.gear]

    @property
    def gear_text(self) -> str:
        return str(self.manual_gear) if self.gear == "M" else self.gear

    @property
    def mode_code(self) -> int:
        return MODE_CODE[self.driving_mode]

    @property
    def steering_code(self) -> int:
        return STEERING_CODE[self.steering_setting]

    @property
    def any_door_open(self) -> bool:
        return any(self.doors.values())

    @property
    def headlight_on(self) -> bool:
        return any(self.lights.values())

    @property
    def reverse_light(self) -> bool:
        return self.gear == "R"

    @property
    def brake_light(self) -> bool:
        return self.brake > 0.05 or self.emergency_brake

    @property
    def active_left_indicator(self) -> bool:
        return (self.left_indicator or self.hazard) and self.blink_on

    @property
    def active_right_indicator(self) -> bool:
        return (self.right_indicator or self.hazard) and self.blink_on

    @property
    def fuel_low(self) -> bool:
        return self.fuel_percent <= FUEL_LOW_PERCENT

    @property
    def engine_hot(self) -> bool:
        return self.engine_temp_c >= ENGINE_HOT_C

    @property
    def battery_low(self) -> bool:
        return self.battery_v < BATTERY_LOW_V

    def tyre_status(self, key: str) -> str:
        pressure = self.tyre_pressures_bar[key]
        if pressure < TYRE_LOW_BAR:
            return "LOW"
        if pressure > TYRE_HIGH_BAR:
            return "HIGH"
        return "NORMAL"

    @property
    def tyre_warning(self) -> bool:
        return any(self.tyre_status(key) != "NORMAL" for key in TYRE_KEYS)

    @property
    def warnings(self) -> list[str]:
        items: list[str] = []
        if self.fuel_low:
            items.append("LOW FUEL")
        if self.engine_hot:
            items.append("ENGINE HOT")
        if self.battery_low:
            items.append("LOW BATTERY")
        if self.any_door_open:
            items.append("DOOR OPEN")
        if self.bonnet:
            items.append("BONNET OPEN")
        if self.boot:
            items.append("BOOT OPEN")
        if self.tyre_warning:
            items.append("TYRE PRESSURE")
        if not self.seatbelt:
            items.append("FASTEN SEATBELT")
        if self.parking_brake and self.speed_abs > 1.0:
            items.append("PARK BRAKE")
        return items

    @property
    def status_text(self) -> str:
        if not self.engine_on:
            return "ENGINE OFF"
        if self.gear == "P":
            return "PARKED"
        if self.speed_abs < 1.0:
            return "READY"
        return "DRIVING"

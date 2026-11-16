from __future__ import annotations

import time
from dataclasses import dataclass, field

from PySide6.QtCore import QObject, Signal

from can_bus.can_decoder import DecodedFrame
from can_bus.message_definitions import GEAR_ENUM, MODE_ENUM, STEERING_ENUM
from can_bus.message_ids import CanId
from config.settings import (
    BATTERY_LOW_V,
    ENGINE_HOT_C,
    FUEL_LOW_PERCENT,
    LINK_TIMEOUT_S,
    TYRE_HIGH_BAR,
    TYRE_LOW_BAR,
)


def _doors() -> dict[str, bool]:
    return {"fl": False, "fr": False, "rl": False, "rr": False}


def _lights() -> dict[str, bool]:
    return {"low_beam": False, "high_beam": False, "drl": False, "fog": False}


def _tyres() -> dict[str, float]:
    return {"fl": 0.0, "fr": 0.0, "rl": 0.0, "rr": 0.0}


@dataclass
class VehicleSnapshot:
    now: float = 0.0
    link: bool = False
    link_age_s: float = 0.0
    frames_total: int = 0
    invalid_total: int = 0
    rx_rate: float = 0.0
    speed_kmh: float = 0.0
    rpm: float = 0.0
    engine_temp_c: float = 0.0
    fuel_percent: float = 0.0
    gear: str = "P"
    manual_gear: int = 1
    clutch: float = 0.0
    engine_load: float = 0.0
    driving_mode: str = "COMFORT"
    steering_setting: str = "COMFORT"
    steering_angle: float = 0.0
    left_indicator: bool = False
    right_indicator: bool = False
    hazard: bool = False
    low_beam: bool = False
    high_beam: bool = False
    drl: bool = False
    fog: bool = False
    reverse_light: bool = False
    brake_pressed: bool = False
    brake_light: bool = False
    engine_running: bool = False
    check_engine: bool = False
    oil_pressure_warning: bool = False
    coolant_warning: bool = False
    battery_v: float = 0.0
    tyre_pressure: dict[str, float] = field(default_factory=_tyres)
    tyre_temp: dict[str, float] = field(default_factory=_tyres)
    doors: dict[str, bool] = field(default_factory=_doors)
    lights: dict[str, bool] = field(default_factory=_lights)
    bonnet: bool = False
    boot: bool = False
    mirror_l: bool = False
    mirror_r: bool = False
    ambient_temp_c: float = 0.0
    odometer_km: float = 0.0
    trip_km: float = 0.0
    avg_speed_kmh: float = 0.0
    instant_consumption: float = 0.0
    avg_consumption: float = 0.0
    trip_duration_s: int = 0
    horn: bool = False
    seatbelt: bool = True
    parking_brake: bool = False
    warnings: list[str] = field(default_factory=list)

    @property
    def speed_abs(self) -> float:
        return abs(self.speed_kmh)

    @property
    def any_door_open(self) -> bool:
        return any(self.doors.values())

    @property
    def headlight_on(self) -> bool:
        return self.low_beam or self.high_beam or self.drl or self.fog

    @property
    def gear_text(self) -> str:
        return f"{self.manual_gear}" if self.gear == "M" else self.gear

    @property
    def tyre_warning(self) -> bool:
        return any(
            value < TYRE_LOW_BAR or value > TYRE_HIGH_BAR
            for value in self.tyre_pressure.values()
            if value > 0
        )

    @property
    def fuel_low(self) -> bool:
        return self.fuel_percent <= FUEL_LOW_PERCENT

    @property
    def battery_low(self) -> bool:
        return self.battery_v < BATTERY_LOW_V

    @property
    def engine_hot(self) -> bool:
        return self.engine_temp_c >= ENGINE_HOT_C


class VehicleModel(QObject):
    updated = Signal(object)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._last_rx: dict[int, float] = {}
        self._last_any = 0.0
        self._started = 0.0
        self._frames = 0
        self._invalid = 0
        self._rx_windows: list[tuple[float, int]] = []
        self._values: dict[str, object] = {
            "speed_kmh": 0.0,
            "rpm": 0.0,
            "engine_temp_c": 0.0,
            "fuel_percent": 0.0,
            "gear": "P",
            "manual_gear": 1,
            "clutch": 0.0,
            "engine_load": 0.0,
            "driving_mode": "COMFORT",
            "steering_setting": "COMFORT",
            "steering_angle": 0.0,
            "left_indicator": False,
            "right_indicator": False,
            "hazard": False,
            "low_beam": False,
            "high_beam": False,
            "drl": False,
            "fog": False,
            "reverse_light": False,
            "brake_pressed": False,
            "brake_light": False,
            "engine_running": False,
            "check_engine": False,
            "oil_pressure_warning": False,
            "coolant_warning": False,
            "battery_v": 0.0,
            "ambient_temp_c": 0.0,
            "odometer_km": 0.0,
            "trip_km": 0.0,
            "avg_speed_kmh": 0.0,
            "instant_consumption": 0.0,
            "avg_consumption": 0.0,
            "trip_duration_s": 0,
            "horn": False,
            "seatbelt": True,
            "parking_brake": False,
        }
        self._tyre_pressure = _tyres()
        self._tyre_temp = _tyres()
        self._doors = _doors()
        self._lights = _lights()
        self._bonnet = False
        self._boot = False
        self._mirror_l = False
        self._mirror_r = False
        self.last_frame: DecodedFrame | None = None
        self.last_frames: list[DecodedFrame] = []

    def ingest(self, frame: DecodedFrame) -> None:
        now = time.monotonic()
        if self._started == 0.0:
            self._started = now
        self._frames += 1
        if not frame.valid:
            self._invalid += 1
        if frame.spec is None:
            return
        self._last_rx[frame.can_id] = now
        self._last_any = now
        self.last_frame = frame
        self.last_frames.append(frame)
        if len(self.last_frames) > 400:
            del self.last_frames[:100]
        self._rx_windows.append((now, self._frames))
        while self._rx_windows and now - self._rx_windows[0][0] > 2.0:
            self._rx_windows.pop(0)
        if not frame.valid:
            return
        values = frame.values
        can_id = frame.can_id
        if can_id == CanId.VEHICLE_SPEED:
            self._values["speed_kmh"] = values["speed"]
        elif can_id == CanId.ENGINE_RPM:
            self._values["rpm"] = values["rpm"]
        elif can_id == CanId.ENGINE_TEMPERATURE:
            self._values["engine_temp_c"] = values["engine_temp"]
        elif can_id == CanId.FUEL_LEVEL:
            self._values["fuel_percent"] = values["fuel_level"]
        elif can_id == CanId.GEAR_POSITION:
            gear = GEAR_ENUM.get(int(values["gear"]), "P")
            self._values["gear"] = gear
            self._values["manual_gear"] = int(values["manual_gear"])
        elif can_id == CanId.TURN_INDICATORS:
            self._values["left_indicator"] = values["left_indicator"]
            self._values["right_indicator"] = values["right_indicator"]
            self._values["hazard"] = values["hazard"]
        elif can_id == CanId.HEADLIGHTS:
            for key in ("low_beam", "high_beam", "drl", "fog", "reverse_light"):
                self._values[key] = values[key]
                if key in self._lights:
                    self._lights[key] = bool(values[key])
        elif can_id == CanId.BRAKE_STATUS:
            self._values["brake_pressed"] = values["brake_pressed"]
            self._values["brake_light"] = values["brake_light"]
        elif can_id == CanId.ENGINE_STATUS:
            self._values["engine_running"] = values["engine_running"]
            self._values["check_engine"] = values["check_engine"]
            self._values["oil_pressure_warning"] = values["oil_pressure"]
            self._values["coolant_warning"] = values["coolant_warning"]
        elif can_id == CanId.BATTERY_VOLTAGE:
            self._values["battery_v"] = values["battery_voltage"]
        elif can_id == CanId.TYRE_PRESSURE:
            self._tyre_pressure = {
                "fl": float(values["tyre_fl"]),
                "fr": float(values["tyre_fr"]),
                "rl": float(values["tyre_rl"]),
                "rr": float(values["tyre_rr"]),
            }
        elif can_id == CanId.BODY_STATUS:
            self._doors = {
                "fl": bool(values["door_fl"]),
                "fr": bool(values["door_fr"]),
                "rl": bool(values["door_rl"]),
                "rr": bool(values["door_rr"]),
            }
            self._bonnet = bool(values["bonnet"])
            self._boot = bool(values["boot"])
            self._mirror_l = bool(values["mirror_l"])
            self._mirror_r = bool(values["mirror_r"])
        elif can_id == CanId.CLUTCH_STATUS:
            self._values["clutch"] = values["clutch"]
        elif can_id == CanId.DRIVING_MODE:
            self._values["driving_mode"] = MODE_ENUM.get(
                int(values["driving_mode"]), "COMFORT"
            )
        elif can_id == CanId.AMBIENT_TEMPERATURE:
            self._values["ambient_temp_c"] = values["ambient_temp"]
        elif can_id == CanId.STEERING_ANGLE:
            self._values["steering_angle"] = values["steering_angle"]
        elif can_id == CanId.ODOMETER_TRIP:
            self._values["odometer_km"] = values["odometer"]
            self._values["trip_km"] = values["trip_distance"]
        elif can_id == CanId.DRIVING_INFO:
            self._values["avg_speed_kmh"] = values["avg_speed"]
            self._values["instant_consumption"] = values["instant_consumption"]
            self._values["avg_consumption"] = values["avg_consumption"]
            self._values["trip_duration_s"] = int(values["trip_duration"])
        elif can_id == CanId.HORN:
            self._values["horn"] = values["horn"]
        elif can_id == CanId.TYRE_TEMPERATURE:
            self._tyre_temp = {
                "fl": float(values["tyre_temp_fl"]),
                "fr": float(values["tyre_temp_fr"]),
                "rl": float(values["tyre_temp_rl"]),
                "rr": float(values["tyre_temp_rr"]),
            }
        elif can_id == CanId.ENGINE_LOAD:
            self._values["engine_load"] = values["engine_load"]
        elif can_id == CanId.STEERING_SETTING:
            self._values["steering_setting"] = STEERING_ENUM.get(
                int(values["steering_setting"]), "COMFORT"
            )
        elif can_id == CanId.CABIN_STATUS:
            self._values["seatbelt"] = values["seatbelt"]
            self._values["parking_brake"] = values["parking_brake"]

    def _rx_rate(self, now: float) -> float:
        if len(self._rx_windows) < 2:
            return 0.0
        first_time, first_count = self._rx_windows[0]
        span = max(0.001, now - first_time)
        return (self._frames - first_count) / span if span >= 0.5 else 0.0

    def snapshot(self, now: float | None = None) -> VehicleSnapshot:
        now = time.monotonic() if now is None else now
        age = now - self._last_any if self._last_any else float("inf")
        link = bool(self._last_any) and age <= LINK_TIMEOUT_S
        values = self._values
        snapshot = VehicleSnapshot(
            now=now,
            link=link,
            link_age_s=age,
            frames_total=self._frames,
            invalid_total=self._invalid,
            rx_rate=self._rx_rate(now),
            speed_kmh=float(values["speed_kmh"]),
            rpm=float(values["rpm"]),
            engine_temp_c=float(values["engine_temp_c"]),
            fuel_percent=float(values["fuel_percent"]),
            gear=str(values["gear"]),
            manual_gear=int(values["manual_gear"]),
            clutch=float(values["clutch"]),
            engine_load=float(values["engine_load"]),
            driving_mode=str(values["driving_mode"]),
            steering_setting=str(values["steering_setting"]),
            steering_angle=float(values["steering_angle"]),
            left_indicator=bool(values["left_indicator"]),
            right_indicator=bool(values["right_indicator"]),
            hazard=bool(values["hazard"]),
            low_beam=bool(values["low_beam"]),
            high_beam=bool(values["high_beam"]),
            drl=bool(values["drl"]),
            fog=bool(values["fog"]),
            reverse_light=bool(values["reverse_light"]),
            brake_pressed=bool(values["brake_pressed"]),
            brake_light=bool(values["brake_light"]),
            engine_running=bool(values["engine_running"]),
            check_engine=bool(values["check_engine"]),
            oil_pressure_warning=bool(values["oil_pressure_warning"]),
            coolant_warning=bool(values["coolant_warning"]),
            battery_v=float(values["battery_v"]),
            tyre_pressure=dict(self._tyre_pressure),
            tyre_temp=dict(self._tyre_temp),
            doors=dict(self._doors),
            lights=dict(self._lights),
            bonnet=self._bonnet,
            boot=self._boot,
            mirror_l=self._mirror_l,
            mirror_r=self._mirror_r,
            ambient_temp_c=float(values["ambient_temp_c"]),
            odometer_km=float(values["odometer_km"]),
            trip_km=float(values["trip_km"]),
            avg_speed_kmh=float(values["avg_speed_kmh"]),
            instant_consumption=float(values["instant_consumption"]),
            avg_consumption=float(values["avg_consumption"]),
            trip_duration_s=int(values["trip_duration_s"]),
            horn=bool(values["horn"]),
            seatbelt=bool(values["seatbelt"]),
            parking_brake=bool(values["parking_brake"]),
        )
        if not link:
            snapshot.warnings.append("NO CAN LINK")
        if snapshot.fuel_low:
            snapshot.warnings.append("LOW FUEL")
        if snapshot.engine_hot:
            snapshot.warnings.append("ENGINE HOT")
        if snapshot.battery_low and snapshot.battery_v > 0:
            snapshot.warnings.append("LOW BATTERY")
        if snapshot.any_door_open:
            snapshot.warnings.append("DOOR OPEN")
        if snapshot.bonnet:
            snapshot.warnings.append("BONNET OPEN")
        if snapshot.boot:
            snapshot.warnings.append("BOOT OPEN")
        if snapshot.tyre_warning:
            snapshot.warnings.append("TYRE PRESSURE")
        if not snapshot.seatbelt:
            snapshot.warnings.append("FASTEN SEATBELT")
        if snapshot.parking_brake and snapshot.speed_abs > 1.0:
            snapshot.warnings.append("PARK BRAKE")
        if snapshot.check_engine:
            snapshot.warnings.append("CHECK ENGINE")
        if snapshot.oil_pressure_warning:
            snapshot.warnings.append("OIL PRESSURE")
        if snapshot.coolant_warning:
            snapshot.warnings.append("COOLANT")
        return snapshot

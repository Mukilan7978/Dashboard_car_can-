from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .message_ids import CanId

GEAR_ENUM: Mapping[int, str] = {0: "P", 1: "R", 2: "N", 3: "D", 4: "M"}
MODE_ENUM: Mapping[int, str] = {0: "ECO", 1: "COMFORT", 2: "SPORT", 3: "SPORT PLUS"}
STEERING_ENUM: Mapping[int, str] = {0: "COMFORT", 1: "SPORT"}
MODE_TO_CODE = {v: k for k, v in MODE_ENUM.items()}
STEERING_TO_CODE = {v: k for k, v in STEERING_ENUM.items()}
GEAR_TO_CODE = {v: k for k, v in GEAR_ENUM.items()}


@dataclass(frozen=True)
class SignalSpec:
    name: str
    byte: int
    fmt: str = "B"
    bit: int | None = None
    scale: float = 1.0
    offset: float = 0.0
    unit: str = ""
    min_value: float | None = None
    max_value: float | None = None
    enum: Mapping[int, str] | None = None
    decimals: int | None = None

    @property
    def is_bit(self) -> bool:
        return self.bit is not None

    @property
    def is_enum(self) -> bool:
        return self.enum is not None

    def format_number(self, value: float) -> str:
        if self.decimals is not None:
            places = self.decimals
        elif self.scale >= 1:
            places = 0
        elif self.scale >= 0.1:
            places = 1
        elif self.scale >= 0.01:
            places = 2
        else:
            places = 3
        return f"{value:.{places}f}"


@dataclass(frozen=True)
class MessageSpec:
    can_id: int
    name: str
    source: str
    dlc: int
    period_ms: int
    timeout_ms: int
    signals: tuple[SignalSpec, ...]
    description: str = ""

    @property
    def period_s(self) -> float:
        return self.period_ms / 1000.0

    @property
    def timeout_s(self) -> float:
        return self.timeout_ms / 1000.0

    @property
    def id_hex(self) -> str:
        return f"0x{self.can_id:03X}"


def _sig(name: str, byte: int, fmt: str = "B", **kw: object) -> SignalSpec:
    return SignalSpec(name, byte, fmt, **kw)  # type: ignore[arg-type]


def _bits(byte: int, prefix: str, names: tuple[str, ...]) -> tuple[SignalSpec, ...]:
    return tuple(_sig(f"{prefix}{n}", byte, bit=i) for i, n in enumerate(names))


def _msg(cid: CanId, name: str, source: str, dlc: int, period: int,
         timeout: int, signals: tuple[SignalSpec, ...], desc: str = "") -> MessageSpec:
    return MessageSpec(cid, name, source, dlc, period, timeout, signals, desc)


SPECS: list[MessageSpec] = [
    _msg(CanId.VEHICLE_SPEED, "Vehicle speed", "ENGINE", 2, 20, 500, (
        _sig("speed", 0, "H", scale=0.01, unit="km/h", min_value=0, max_value=260, decimals=1),
    ), "Absolute vehicle speed."),
    _msg(CanId.ENGINE_RPM, "Engine RPM", "ENGINE", 2, 20, 500, (
        _sig("rpm", 0, "H", unit="rpm", min_value=0, max_value=8000, decimals=0),
    ), "Engine crankshaft speed."),
    _msg(CanId.ENGINE_TEMPERATURE, "Engine temperature", "ENGINE", 2, 1000, 3000, (
        _sig("engine_temp", 0, "h", scale=0.1, unit="°C", min_value=-40, max_value=150, decimals=1),
    )),
    _msg(CanId.FUEL_LEVEL, "Fuel level", "ENGINE", 2, 1000, 3000, (
        _sig("fuel_level", 0, "H", scale=0.1, unit="%", min_value=0, max_value=100, decimals=1),
    )),
    _msg(CanId.GEAR_POSITION, "Gear position", "TRANSMISSION", 2, 50, 1000, (
        _sig("gear", 0, "B", enum=GEAR_ENUM),
        _sig("manual_gear", 1, "B", min_value=1, max_value=8, decimals=0),
    )),
    _msg(CanId.TURN_INDICATORS, "Turn indicators", "BCM", 1, 100, 1000,
         _bits(0, "", ("left_indicator", "right_indicator", "hazard"))),
    _msg(CanId.HEADLIGHTS, "Headlights", "BCM", 1, 200, 2000,
         _bits(0, "", ("low_beam", "high_beam", "drl", "fog", "reverse_light"))),
    _msg(CanId.BRAKE_STATUS, "Brake status", "BCM", 1, 50, 1000,
         _bits(0, "", ("brake_pressed", "brake_light"))),
    _msg(CanId.ENGINE_STATUS, "Engine status", "ENGINE", 1, 100, 2000,
         _bits(0, "", ("engine_running", "check_engine", "oil_pressure", "coolant_warning"))),
    _msg(CanId.BATTERY_VOLTAGE, "Battery voltage", "ENGINE", 2, 1000, 3000, (
        _sig("battery_voltage", 0, "H", scale=0.001, unit="V", min_value=8, max_value=16, decimals=2),
    )),
    _msg(CanId.TYRE_PRESSURE, "Tyre pressure", "BCM", 8, 1000, 3000, (
        _sig("tyre_fl", 0, "H", scale=0.001, unit="bar", min_value=0, max_value=5, decimals=2),
        _sig("tyre_fr", 2, "H", scale=0.001, unit="bar", min_value=0, max_value=5, decimals=2),
        _sig("tyre_rl", 4, "H", scale=0.001, unit="bar", min_value=0, max_value=5, decimals=2),
        _sig("tyre_rr", 6, "H", scale=0.001, unit="bar", min_value=0, max_value=5, decimals=2),
    )),
    _msg(CanId.BODY_STATUS, "Body status", "BCM", 1, 200, 2000,
         _bits(0, "", ("door_fl", "door_fr", "door_rl", "door_rr",
                       "bonnet", "boot", "mirror_l", "mirror_r"))),
    _msg(CanId.CLUTCH_STATUS, "Clutch status", "TRANSMISSION", 1, 50, 1000, (
        _sig("clutch", 0, "B", unit="%", min_value=0, max_value=100, decimals=0),
    )),
    _msg(CanId.DRIVING_MODE, "Driving mode", "ENGINE", 1, 1000, 3000, (
        _sig("driving_mode", 0, "B", enum=MODE_ENUM),
    )),
    _msg(CanId.AMBIENT_TEMPERATURE, "Ambient temperature", "BCM", 2, 1000, 5000, (
        _sig("ambient_temp", 0, "h", scale=0.1, unit="°C", min_value=-40, max_value=60, decimals=1),
    )),
    _msg(CanId.STEERING_ANGLE, "Steering angle", "BCM", 2, 20, 500, (
        _sig("steering_angle", 0, "h", scale=0.1, unit="°", min_value=-540, max_value=540, decimals=1),
    )),
    _msg(CanId.ODOMETER_TRIP, "Odometer and trip", "ENGINE", 8, 1000, 3000, (
        _sig("odometer", 0, "I", scale=0.1, unit="km", min_value=0, max_value=999999, decimals=1),
        _sig("trip_distance", 4, "I", scale=0.1, unit="km", min_value=0, max_value=9999, decimals=1),
    )),
    _msg(CanId.DRIVING_INFO, "Driving information", "ENGINE", 8, 1000, 3000, (
        _sig("avg_speed", 0, "H", scale=0.1, unit="km/h", min_value=0, max_value=260, decimals=1),
        _sig("instant_consumption", 2, "H", scale=0.01, unit="L/100km", min_value=0, max_value=99, decimals=1),
        _sig("avg_consumption", 4, "H", scale=0.01, unit="L/100km", min_value=0, max_value=99, decimals=1),
        _sig("trip_duration", 6, "H", unit="s", min_value=0, max_value=65535, decimals=0),
    )),
    _msg(CanId.HORN, "Horn", "BCM", 1, 100, 1000, _bits(0, "", ("horn",))),
    _msg(CanId.TYRE_TEMPERATURE, "Tyre temperature", "BCM", 4, 1000, 3000, (
        _sig("tyre_temp_fl", 0, "b", offset=-40, unit="°C", min_value=-40, max_value=85, decimals=0),
        _sig("tyre_temp_fr", 1, "b", offset=-40, unit="°C", min_value=-40, max_value=85, decimals=0),
        _sig("tyre_temp_rl", 2, "b", offset=-40, unit="°C", min_value=-40, max_value=85, decimals=0),
        _sig("tyre_temp_rr", 3, "b", offset=-40, unit="°C", min_value=-40, max_value=85, decimals=0),
    )),
    _msg(CanId.ENGINE_LOAD, "Engine load", "ENGINE", 1, 50, 1000, (
        _sig("engine_load", 0, "B", unit="%", min_value=0, max_value=100, decimals=0),
    )),
    _msg(CanId.STEERING_SETTING, "Steering setting", "BCM", 1, 1000, 3000, (
        _sig("steering_setting", 0, "B", enum=STEERING_ENUM),
    )),
    _msg(CanId.CABIN_STATUS, "Cabin status", "BCM", 1, 1000, 3000,
         _bits(0, "", ("seatbelt", "parking_brake"))),
    _msg(CanId.ACCELERATOR_PEDAL, "Accelerator pedal position", "ENGINE", 8, 50, 1000, (
        _sig("accelerator", 0, "H", scale=0.1, unit="%", min_value=0, max_value=100, decimals=0),
    )),
    _msg(CanId.BRAKE_PEDAL, "Brake pedal position", "ENGINE", 8, 50, 1000, (
        _sig("brake", 0, "B", unit="%", min_value=0, max_value=100, decimals=0),
    )),
    _msg(CanId.STEERING_INPUT, "Steering input", "ENGINE", 8, 50, 1000, (
        _sig("steering", 0, "H", min_value=-540, max_value=540, decimals=0),
    )),
    _msg(CanId.CLUTCH_PEDAL, "Clutch pedal position", "ENGINE", 8, 50, 1000, (
        _sig("clutch", 0, "B", unit="%", min_value=0, max_value=100, decimals=0),
    )),
]

BY_ID: dict[int, MessageSpec] = {spec.can_id: spec for spec in SPECS}
MESSAGE_SPECS = SPECS
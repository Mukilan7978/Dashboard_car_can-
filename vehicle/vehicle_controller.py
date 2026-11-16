from __future__ import annotations

from typing import Any

from .vehicle_state import (
    DOOR_KEYS,
    LIGHT_KEYS,
    MODE_CODE,
    STEERING_CODE,
    VehicleState,
)

HEARTBEAT_TIMEOUT_S = 2.0
GEAR_ORDER = ("P", "R", "N", "D", "M")
HELD_INPUTS = ("throttle", "brake", "clutch", "steering", "horn", "emergency_brake")


class VehicleController:
    def __init__(self, state: VehicleState) -> None:
        self.state = state
        self._last_heartbeat: float | None = None

    def apply(self, command: dict[str, Any], now: float) -> None:
        action = command.get("cmd")
        if action == "ping":
            return
        if action == "heartbeat":
            self._last_heartbeat = now
            return
        if action == "input":
            self._apply_input(command.get("name"), command.get("value"))
            return
        if action == "release_all":
            self._release_all()
            return
        if action == "engine_toggle":
            self._set_engine(not self.state.engine_on)
            return
        if action == "engine_start":
            self._set_engine(True)
            return
        if action == "engine_stop":
            self._set_engine(False)
            return
        if action == "gear_next":
            self._gear_next()
            return
        if action == "gear_prev":
            self._gear_prev()
            return
        if action == "gear_cycle_mode":
            self._gear_cycle_mode()
            return
        if action == "set_gear":
            self._set_gear(str(command.get("value", "")).upper())
            return
        if action == "indicator":
            self._set_indicator(str(command.get("value", "")))
            return
        if action == "hazard_toggle":
            self.state.hazard = not self.state.hazard
            if self.state.hazard:
                self.state.left_indicator = False
                self.state.right_indicator = False
            return
        if action == "light_toggle":
            key = str(command.get("value", ""))
            if key in LIGHT_KEYS:
                self.state.lights[key] = not self.state.lights[key]
            return
        if action == "all_lights_off":
            for key in LIGHT_KEYS:
                self.state.lights[key] = False
            return
        if action == "door_toggle":
            key = str(command.get("value", ""))
            if key in DOOR_KEYS:
                self.state.doors[key] = not self.state.doors[key]
            return
        if action == "mirror_toggle":
            key = str(command.get("value", ""))
            if key in ("l", "r"):
                self.state.mirrors[key] = not self.state.mirrors[key]
            return
        if action == "bonnet_toggle":
            self.state.bonnet = not self.state.bonnet
            return
        if action == "boot_toggle":
            self.state.boot = not self.state.boot
            return
        if action == "mode_set":
            self._set_mode(command.get("value"))
            return
        if action == "steering_setting":
            self._set_steering(command.get("value"))
            return
        if action == "trip_reset":
            self._reset_trip()
            return
        if action == "seatbelt_toggle":
            self.state.seatbelt = not self.state.seatbelt
            return
        if action == "parking_brake_toggle":
            self.state.parking_brake = not self.state.parking_brake
            return
        if action == "close_all":
            for key in DOOR_KEYS:
                self.state.doors[key] = False
            self.state.bonnet = False
            self.state.boot = False
            self.state.mirrors["l"] = False
            self.state.mirrors["r"] = False
            return

    def decay(self, now: float) -> None:
        if self._last_heartbeat is None:
            return
        if now - self._last_heartbeat > HEARTBEAT_TIMEOUT_S:
            self._release_all()

    def _set_engine(self, running: bool) -> None:
        self.state.engine_on = running
        if not running:
            self.state.throttle = 0.0

    def _apply_input(self, name: Any, value: Any) -> None:
        name = str(name)
        if name in ("throttle", "brake"):
            setattr(self.state, name, 1.0 if bool(value) else 0.0)
        elif name == "clutch":
            self.state.clutch = 100.0 if bool(value) else 0.0
        elif name == "steering":
            try:
                self.state.steering_input = max(-1.0, min(1.0, float(value)))
            except (TypeError, ValueError):
                self.state.steering_input = 0.0
        elif name == "horn":
            self.state.horn = bool(value)
        elif name == "emergency_brake":
            self.state.emergency_brake = bool(value)

    def _release_all(self) -> None:
        self.state.throttle = 0.0
        self.state.brake = 0.0
        self.state.clutch = 0.0
        self.state.steering_input = 0.0
        self.state.horn = False
        self.state.emergency_brake = False

    def _set_gear(self, gear: str) -> None:
        if gear not in GEAR_ORDER:
            return
        moving = abs(self.state.speed_kmh) > 5.0
        if moving and gear in ("P", "R"):
            return
        if gear == "P":
            self.state.speed_kmh = 0.0
            self.state.manual_gear = 1
            self.state.parking_brake = True
        elif gear == "M":
            if self.state.gear not in ("D", "M"):
                self.state.manual_gear = 1
            self.state.parking_brake = False
        elif gear == "D":
            self.state.manual_gear = 1
            self.state.parking_brake = False
        elif gear == "N":
            self.state.parking_brake = False
        elif gear == "R":
            self.state.parking_brake = False
        self.state.gear = gear

    def _gear_next(self) -> None:
        if self.state.gear == "M":
            self.state.manual_gear = min(8, self.state.manual_gear + 1)
            return
        order = ("N", "D", "M") if abs(self.state.speed_kmh) > 5.0 else GEAR_ORDER
        if self.state.gear not in order:
            self._set_gear("D")
            return
        index = (order.index(self.state.gear) + 1) % len(order)
        self._set_gear(order[index])

    def _gear_prev(self) -> None:
        if self.state.gear == "M":
            self.state.manual_gear = max(1, self.state.manual_gear - 1)
            return
        order = ("N", "D", "M") if abs(self.state.speed_kmh) > 5.0 else GEAR_ORDER
        if self.state.gear not in order:
            self._set_gear("D")
            return
        index = (order.index(self.state.gear) - 1) % len(order)
        self._set_gear(order[index])

    def _gear_cycle_mode(self) -> None:
        order = ("N", "D", "M") if abs(self.state.speed_kmh) > 5.0 else GEAR_ORDER
        if self.state.gear not in order:
            self._set_gear("D")
            return
        index = (order.index(self.state.gear) + 1) % len(order)
        self._set_gear(order[index])

    def _set_indicator(self, side: str) -> None:
        if side == "left":
            self.state.left_indicator = not self.state.left_indicator
            self.state.right_indicator = False
            self.state.hazard = False
        elif side == "right":
            self.state.right_indicator = not self.state.right_indicator
            self.state.left_indicator = False
            self.state.hazard = False
        elif side == "off":
            self.state.left_indicator = False
            self.state.right_indicator = False
            self.state.hazard = False

    def _set_mode(self, value: Any) -> None:
        if isinstance(value, int):
            for name, code in MODE_CODE.items():
                if code == value:
                    self.state.driving_mode = name
                    return
            return
        name = str(value).upper()
        if name in MODE_CODE:
            self.state.driving_mode = name

    def _set_steering(self, value: Any) -> None:
        if isinstance(value, int):
            for name, code in STEERING_CODE.items():
                if code == value:
                    self.state.steering_setting = name
                    return
            return
        name = str(value).upper()
        if name in STEERING_CODE:
            self.state.steering_setting = name

    def _reset_trip(self) -> None:
        self.state.trip_km = 0.0
        self.state.trip_duration_s = 0.0
        self.state.fuel_used_l = 0.0
        self.state.avg_speed_kmh = 0.0
        self.state.avg_consumption = 0.0
        self.state.instant_consumption = 0.0

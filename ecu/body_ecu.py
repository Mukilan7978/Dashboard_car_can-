from __future__ import annotations

from typing import Any

from can_bus.message_ids import CanId
from vehicle.vehicle_state import VehicleState
from .base_ecu import BaseECU


class BodyECU(BaseECU):
    name = "BCM"
    message_ids = (
        CanId.TURN_INDICATORS,
        CanId.HEADLIGHTS,
        CanId.BRAKE_STATUS,
        CanId.TYRE_PRESSURE,
        CanId.BODY_STATUS,
        CanId.AMBIENT_TEMPERATURE,
        CanId.STEERING_ANGLE,
        CanId.HORN,
        CanId.TYRE_TEMPERATURE,
        CanId.STEERING_SETTING,
        CanId.CABIN_STATUS,
    )

    def build(self, state: VehicleState, can_id: int) -> dict[str, Any] | None:
        if can_id == CanId.TURN_INDICATORS:
            return {
                "left_indicator": state.active_left_indicator,
                "right_indicator": state.active_right_indicator,
                "hazard": state.hazard,
            }
        if can_id == CanId.HEADLIGHTS:
            return {
                "low_beam": state.lights["low_beam"],
                "high_beam": state.lights["high_beam"],
                "drl": state.lights["drl"],
                "fog": state.lights["fog"],
                "reverse_light": state.reverse_light,
            }
        if can_id == CanId.BRAKE_STATUS:
            return {
                "brake_pressed": state.brake > 0.05 or state.emergency_brake,
                "brake_light": state.brake_light,
            }
        if can_id == CanId.TYRE_PRESSURE:
            return {
                "tyre_fl": state.tyre_pressures_bar["fl"],
                "tyre_fr": state.tyre_pressures_bar["fr"],
                "tyre_rl": state.tyre_pressures_bar["rl"],
                "tyre_rr": state.tyre_pressures_bar["rr"],
            }
        if can_id == CanId.BODY_STATUS:
            return {
                "door_fl": state.doors["fl"],
                "door_fr": state.doors["fr"],
                "door_rl": state.doors["rl"],
                "door_rr": state.doors["rr"],
                "bonnet": state.bonnet,
                "boot": state.boot,
                "mirror_l": state.mirrors["l"],
                "mirror_r": state.mirrors["r"],
            }
        if can_id == CanId.AMBIENT_TEMPERATURE:
            return {"ambient_temp": state.ambient_temp_c}
        if can_id == CanId.STEERING_ANGLE:
            return {"steering_angle": state.steering_angle}
        if can_id == CanId.HORN:
            return {"horn": state.horn}
        if can_id == CanId.TYRE_TEMPERATURE:
            return {
                "tyre_temp_fl": state.tyre_temps_c["fl"],
                "tyre_temp_fr": state.tyre_temps_c["fr"],
                "tyre_temp_rl": state.tyre_temps_c["rl"],
                "tyre_temp_rr": state.tyre_temps_c["rr"],
            }
        if can_id == CanId.STEERING_SETTING:
            return {"steering_setting": state.steering_setting}
        if can_id == CanId.CABIN_STATUS:
            return {
                "seatbelt": state.seatbelt,
                "parking_brake": state.parking_brake,
            }
        return None

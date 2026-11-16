from __future__ import annotations

from typing import Any

from can_bus.message_ids import CanId
from vehicle.vehicle_state import VehicleState
from .base_ecu import BaseECU


class EngineECU(BaseECU):
    name = "ENGINE"
    message_ids = (
        CanId.VEHICLE_SPEED,
        CanId.ENGINE_RPM,
        CanId.ENGINE_TEMPERATURE,
        CanId.FUEL_LEVEL,
        CanId.ENGINE_STATUS,
        CanId.BATTERY_VOLTAGE,
        CanId.DRIVING_MODE,
        CanId.ODOMETER_TRIP,
        CanId.DRIVING_INFO,
        CanId.ENGINE_LOAD,
        CanId.ACCELERATOR_PEDAL,
        CanId.BRAKE_PEDAL,
        CanId.STEERING_INPUT,
        CanId.CLUTCH_PEDAL,
    )

    def build(self, state: VehicleState, can_id: int) -> dict[str, Any] | None:
        if can_id == CanId.VEHICLE_SPEED:
            return {"speed": state.speed_abs}
        if can_id == CanId.ENGINE_RPM:
            return {"rpm": state.rpm}
        if can_id == CanId.ENGINE_TEMPERATURE:
            return {"engine_temp": state.engine_temp_c}
        if can_id == CanId.FUEL_LEVEL:
            return {"fuel_level": state.fuel_percent}
        if can_id == CanId.ENGINE_STATUS:
            return {
                "engine_running": state.engine_on,
                "check_engine": False,
                "oil_pressure": False,
                "coolant_warning": state.engine_hot,
            }
        if can_id == CanId.BATTERY_VOLTAGE:
            return {"battery_voltage": state.battery_v}
        if can_id == CanId.DRIVING_MODE:
            return {"driving_mode": state.driving_mode}
        if can_id == CanId.ODOMETER_TRIP:
            return {
                "odometer": min(999999.0, state.odometer_km),
                "trip_distance": min(9999.0, state.trip_km),
            }
        if can_id == CanId.DRIVING_INFO:
            return {
                "avg_speed": min(260.0, state.avg_speed_kmh),
                "instant_consumption": min(99.0, state.instant_consumption),
                "avg_consumption": min(99.0, state.avg_consumption),
                "trip_duration": min(65535, int(state.trip_duration_s)),
            }
        if can_id == CanId.ENGINE_LOAD:
            return {"engine_load": state.engine_load}
        if can_id == CanId.ACCELERATOR_PEDAL:
            return {"accelerator": state.throttle}
        if can_id == CanId.BRAKE_PEDAL:
            return {"brake": state.brake}
        if can_id == CanId.STEERING_INPUT:
            return {"steering": state.steering_input}
        if can_id == CanId.CLUTCH_PEDAL:
            return {"clutch": state.clutch}
        return None

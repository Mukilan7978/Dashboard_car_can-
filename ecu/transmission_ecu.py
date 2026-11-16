from __future__ import annotations

from typing import Any

from can_bus.message_ids import CanId
from vehicle.vehicle_state import VehicleState
from .base_ecu import BaseECU


class TransmissionECU(BaseECU):
    name = "TRANSMISSION"
    message_ids = (
        CanId.GEAR_POSITION,
        CanId.CLUTCH_STATUS,
    )

    def build(self, state: VehicleState, can_id: int) -> dict[str, Any] | None:
        if can_id == CanId.GEAR_POSITION:
            return {"gear": state.gear, "manual_gear": state.manual_gear}
        if can_id == CanId.CLUTCH_STATUS:
            return {"clutch": state.clutch}
        return None

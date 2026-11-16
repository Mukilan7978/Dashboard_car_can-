from __future__ import annotations

from typing import Any, Protocol

from can_bus.message_definitions import BY_ID
from vehicle.vehicle_state import VehicleState


class Transmitter(Protocol):
    def transmit(self, can_id: int, values: dict[str, Any], now: float,
                 source: str) -> bool:
        ...


class BaseECU:
    name = "ECU"
    message_ids: tuple[int, ...] = ()

    def __init__(self, transmitter: Transmitter) -> None:
        self.transmitter = transmitter
        self._next_due: dict[int, float] = {cid: 0.0 for cid in self.message_ids}

    def poll(self, state: VehicleState, now: float) -> None:
        for can_id in self.message_ids:
            if now < self._next_due[can_id]:
                continue
            values = self.build(state, can_id)
            if values is not None:
                self.transmitter.transmit(can_id, values, now, self.name)
            self._next_due[can_id] = now + BY_ID[can_id].period_s

    def build(self, state: VehicleState, can_id: int) -> dict[str, Any] | None:
        raise NotImplementedError

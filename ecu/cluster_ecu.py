from __future__ import annotations

import time

import can

from can_bus.can_decoder import DecodedFrame, decode_message
from can_bus.message_definitions import BY_ID
from can_bus.security_monitor import SecurityMonitor


class ClusterECU:
    name = "CLUSTER"

    def __init__(self, security: SecurityMonitor | None = None) -> None:
        self.security = security
        self.received = 0
        self.rejected = 0
        self.last_seen: dict[int, float] = {}

    def process(self, message: can.Message) -> DecodedFrame | None:
        self.received += 1
        decoded = decode_message(message)
        if self.security is not None:
            self.security.observe(message, decoded)
        if not decoded.valid:
            self.rejected += 1
            return None
        self.last_seen[message.arbitration_id] = time.monotonic()
        return decoded

    def is_stale(self, can_id: int, now: float | None = None) -> bool:
        now = now if now is not None else time.monotonic()
        spec = BY_ID.get(can_id)
        last = self.last_seen.get(can_id)
        if spec is None or last is None:
            return True
        return now - last > spec.timeout_s

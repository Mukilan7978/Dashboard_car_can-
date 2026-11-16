from __future__ import annotations

from typing import Any

import can

from can_bus.can_decoder import decode_message
from can_bus.can_encoder import encode_by_id
from can_bus.can_logger import CanLogger
from can_bus.can_sender import CanSender
from can_bus.message_definitions import BY_ID, SignalSpec
from can_bus.security_monitor import SecurityMonitor


def _validate_signal(signal: SignalSpec, value: Any) -> str | None:
    if signal.is_bit:
        return None
    if signal.is_enum:
        if isinstance(value, str):
            if not any(label == value for label in signal.enum.values()):  # type: ignore[union-attr]
                return f"invalid enum {value!r}"
        else:
            try:
                code = int(value)
            except (TypeError, ValueError):
                return f"invalid enum {value!r}"
            if code not in signal.enum:  # type: ignore[operator]
                return f"invalid enum code {code}"
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return f"invalid number {value!r}"
    if signal.min_value is not None and number < signal.min_value:
        return f"{signal.name} below range ({number})"
    if signal.max_value is not None and number > signal.max_value:
        return f"{signal.name} above range ({number})"
    return None


class GatewayECU:
    name = "GATEWAY"

    def __init__(
        self,
        sender: CanSender | None = None,
        logger: CanLogger | None = None,
        security: SecurityMonitor | None = None,
    ) -> None:
        self.sender = sender
        self.logger = logger
        self.security = security
        self.last_sent: dict[int, float] = {}
        self.transmitted = 0
        self.rejected = 0
        self.invalid_inbound = 0

    def transmit(self, can_id: int, values: dict[str, Any], now: float,
                 source: str) -> bool:
        spec = BY_ID.get(can_id)
        if spec is None:
            self._reject(can_id, source, "unknown CAN ID")
            return False
        if spec.source != source:
            self._reject(can_id, source, f"source {source} does not own ID")
            return False
        minimum_interval = spec.period_s * 0.5
        last = self.last_sent.get(can_id)
        if last is not None and now - last < minimum_interval:
            self._reject(can_id, source, "rate limit exceeded")
            return False
        for signal in spec.signals:
            if signal.name not in values:
                self._reject(can_id, source, f"missing {signal.name}")
                return False
            error = _validate_signal(signal, values[signal.name])
            if error is not None:
                self._reject(can_id, source, error)
                return False
        try:
            message = encode_by_id(can_id, values)
        except (ValueError, TypeError) as error:
            self._reject(can_id, source, f"encode error: {error}")
            return False
        if self.sender is not None and not self.sender.send(message):
            self._reject(can_id, source, "CAN send failed")
            return False
        self.last_sent[can_id] = now
        self.transmitted += 1
        decoded = decode_message(message)
        if self.logger is not None:
            self.logger.log_message(message, decoded)
        if self.security is not None:
            self.security.observe(message, decoded)
        return True

    def validate_inbound(self, message: can.Message) -> tuple[bool, str]:
        spec = BY_ID.get(message.arbitration_id)
        if spec is None:
            self.invalid_inbound += 1
            return False, f"unknown CAN ID 0x{message.arbitration_id:03X}"
        if len(message.data) != spec.dlc:
            self.invalid_inbound += 1
            return False, f"DLC mismatch for 0x{message.arbitration_id:03X}"
        decoded = decode_message(message)
        if not decoded.valid:
            self.invalid_inbound += 1
            return False, decoded.error or "invalid frame"
        return True, ""

    def _reject(self, can_id: int, source: str, reason: str) -> None:
        self.rejected += 1
        if self.logger is not None:
            self.logger.log_event("gateway_reject", reason, can_id, "warning")
        if self.security is not None:
            self.security.note(
                "gateway_reject",
                f"{source} 0x{can_id:03X}: {reason}",
                "warning",
                can_id,
            )

from __future__ import annotations

import struct
import time
from dataclasses import dataclass
from typing import Any

import can

from .message_definitions import BY_ID, MessageSpec


@dataclass
class DecodedFrame:
    can_id: int
    name: str
    source: str
    timestamp: float
    dlc: int
    data: bytes
    values: dict[str, Any]
    raw: dict[str, int]
    text: dict[str, str]
    valid: bool
    error: str | None = None
    spec: MessageSpec | None = None

    @property
    def id_hex(self) -> str:
        return f"0x{self.can_id:03X}"

    @property
    def data_hex(self) -> str:
        return " ".join(f"{byte:02X}" for byte in self.data)

    def value(self, name: str, default: Any = None) -> Any:
        return self.values.get(name, default)

    def is_on(self, name: str) -> bool:
        return bool(self.values.get(name, False))

    def summary(self) -> str:
        return " | ".join(f"{key}={value}" for key, value in self.text.items())


def _text_for(spec: Any, raw: int) -> str:
    if spec.is_bit:
        return "ON" if raw else "OFF"
    if spec.is_enum:
        return spec.enum.get(raw, f"UNKNOWN({raw})")
    physical = raw * spec.scale + spec.offset
    number = spec.format_number(physical)
    return f"{number} {spec.unit}".strip()


def decode_message(msg: can.Message) -> DecodedFrame:
    timestamp = msg.timestamp if msg.timestamp else time.time()
    spec = BY_ID.get(msg.arbitration_id)
    if spec is None:
        return DecodedFrame(
            can_id=msg.arbitration_id,
            name="UNKNOWN",
            source="UNKNOWN",
            timestamp=timestamp,
            dlc=msg.dlc,
            data=bytes(msg.data),
            values={},
            raw={},
            text={},
            valid=False,
            error=f"unknown CAN ID 0x{msg.arbitration_id:03X}",
        )
    data = bytes(msg.data)
    if len(data) != spec.dlc:
        return DecodedFrame(
            can_id=msg.arbitration_id,
            name=spec.name,
            source=spec.source,
            timestamp=timestamp,
            dlc=len(data),
            data=data,
            values={},
            raw={},
            text={},
            valid=False,
            error=f"DLC {len(data)} != {spec.dlc}",
            spec=spec,
        )

    values: dict[str, Any] = {}
    raw_values: dict[str, int] = {}
    text_values: dict[str, str] = {}
    error: str | None = None

    for signal in spec.signals:
        if signal.is_bit:
            raw = (data[signal.byte] >> signal.bit) & 1
            values[signal.name] = bool(raw)
            raw_values[signal.name] = raw
            text_values[signal.name] = "ON" if raw else "OFF"
            continue
        (raw,) = struct.unpack_from("<" + signal.fmt, data, signal.byte)
        raw_values[signal.name] = int(raw)
        text_values[signal.name] = _text_for(signal, int(raw))
        if signal.is_enum:
            values[signal.name] = int(raw)
            if int(raw) not in signal.enum:  # type: ignore[operator]
                error = error or f"invalid enum {raw} for {signal.name}"
        else:
            physical = raw * signal.scale + signal.offset
            values[signal.name] = float(physical)
            if signal.min_value is not None and physical < signal.min_value:
                error = error or f"{signal.name} below range ({physical:.3f})"
            if signal.max_value is not None and physical > signal.max_value:
                error = error or f"{signal.name} above range ({physical:.3f})"

    return DecodedFrame(
        can_id=msg.arbitration_id,
        name=spec.name,
        source=spec.source,
        timestamp=timestamp,
        dlc=len(data),
        data=data,
        values=values,
        raw=raw_values,
        text=text_values,
        valid=error is None,
        error=error,
        spec=spec,
    )

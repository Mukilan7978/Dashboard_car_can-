from __future__ import annotations

import struct
from typing import Any

import can

from .message_definitions import BY_ID, MessageSpec, SignalSpec

_FORMAT_RANGE: dict[str, tuple[int, int]] = {
    "b": (-128, 127),
    "B": (0, 255),
    "h": (-32768, 32767),
    "H": (0, 65535),
    "i": (-2147483648, 2147483647),
    "I": (0, 4294967295),
}


def _enum_code(spec: SignalSpec, value: Any) -> int:
    if isinstance(value, str):
        for code, label in spec.enum.items():  # type: ignore[union-attr]
            if label == value:
                return int(code)
        raise ValueError(f"unknown enum value {value!r} for {spec.name}")
    code = int(value)
    if code not in spec.enum:  # type: ignore[operator]
        raise ValueError(f"unknown enum code {code} for {spec.name}")
    return code


def _raw_value(spec: SignalSpec, value: Any) -> int:
    if spec.is_bit:
        return 1 if bool(value) else 0
    if spec.is_enum:
        return _enum_code(spec, value)
    physical = float(value)
    if spec.min_value is not None:
        physical = max(spec.min_value, physical)
    if spec.max_value is not None:
        physical = min(spec.max_value, physical)
    raw = int(round((physical - spec.offset) / spec.scale))
    low, high = _FORMAT_RANGE[spec.fmt]
    return max(low, min(high, raw))


def encode_message(spec: MessageSpec, values: dict[str, Any]) -> can.Message:
    data = bytearray(spec.dlc)
    bit_bytes: dict[int, int] = {}
    for signal in spec.signals:
        if signal.name not in values:
            raise ValueError(f"missing signal {signal.name} for {spec.name}")
        raw = _raw_value(signal, values[signal.name])
        if signal.is_bit:
            bit_bytes[signal.byte] = bit_bytes.get(signal.byte, 0) | (
                (1 << signal.bit) if raw else 0
            )
        else:
            struct.pack_into("<" + signal.fmt, data, signal.byte, raw)
    for byte, value in bit_bytes.items():
        data[byte] = value
    return can.Message(
        arbitration_id=spec.can_id,
        data=bytes(data),
        is_extended_id=False,
        dlc=spec.dlc,
    )


def encode_by_id(can_id: int, values: dict[str, Any]) -> can.Message:
    spec = BY_ID.get(can_id)
    if spec is None:
        raise ValueError(f"unknown CAN ID 0x{can_id:03X}")
    return encode_message(spec, values)

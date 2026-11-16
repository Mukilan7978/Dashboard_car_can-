from __future__ import annotations

import can
import pytest

from can_bus.can_decoder import decode_message
from can_bus.can_encoder import encode_message
from can_bus.message_definitions import SPECS


def sample_value(signal):
    if signal.is_bit:
        return True
    if signal.is_enum:
        return next(iter(signal.enum.values()))
    if signal.min_value is not None and signal.max_value is not None:
        return (signal.min_value + signal.max_value) / 2.0
    if signal.min_value is not None:
        return signal.min_value
    if signal.max_value is not None:
        return signal.max_value
    return 0.0


@pytest.mark.parametrize("spec", SPECS, ids=[spec.name for spec in SPECS])
def test_every_spec_round_trips(spec):
    values = {signal.name: sample_value(signal) for signal in spec.signals}
    message = encode_message(spec, values)
    assert message.arbitration_id == spec.can_id
    assert message.dlc == spec.dlc
    decoded = decode_message(message)
    assert decoded.valid, decoded.error
    assert decoded.can_id == spec.can_id
    assert decoded.spec is spec
    assert set(decoded.values) == set(values)
    for signal in spec.signals:
        value = decoded.values[signal.name]
        if signal.is_bit:
            assert value is True
        elif signal.is_enum:
            assert value in signal.enum
        else:
            tolerance = max(0.001, abs(signal.scale) * 0.75 + 0.001)
            assert abs(value - values[signal.name]) <= tolerance


def test_decoder_rejects_wrong_dlc():
    spec = next(spec for spec in SPECS if spec.name == "Vehicle speed")
    message = encode_message(spec, {"speed": 50.0})
    broken = can.Message(
        arbitration_id=message.arbitration_id,
        data=bytes(message.data)[:1],
        dlc=1,
        is_extended_id=False,
    )
    decoded = decode_message(broken)
    assert not decoded.valid
    assert "DLC" in (decoded.error or "")


def test_decoder_marks_unknown_id():
    message = can.Message(
        arbitration_id=0x7FF,
        data=bytes([1, 2, 3]),
        dlc=3,
        is_extended_id=False,
    )
    decoded = decode_message(message)
    assert not decoded.valid
    assert decoded.can_id == 0x7FF
    assert "unknown" in (decoded.error or "").lower()

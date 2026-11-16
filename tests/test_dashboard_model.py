from __future__ import annotations

from can_bus.can_decoder import decode_message
from can_bus.can_encoder import encode_by_id
from can_bus.message_ids import CanId
from dashboard.model import VehicleModel


def ingest(model: VehicleModel, can_id: CanId, values: dict) -> None:
    model.ingest(decode_message(encode_by_id(can_id, values)))


def test_model_decodes_snapshot_from_can_frames():
    model = VehicleModel()
    ingest(model, CanId.VEHICLE_SPEED, {"speed": 87.4})
    ingest(model, CanId.ENGINE_RPM, {"rpm": 2850})
    ingest(model, CanId.GEAR_POSITION, {"gear": "D", "manual_gear": 3})
    ingest(model, CanId.FUEL_LEVEL, {"fuel_level": 68.0})
    ingest(model, CanId.DRIVING_MODE, {"driving_mode": "SPORT"})
    ingest(model, CanId.BATTERY_VOLTAGE, {"battery_voltage": 12.6})
    ingest(model, CanId.TURN_INDICATORS, {
        "left_indicator": True, "right_indicator": False, "hazard": False,
    })
    ingest(model, CanId.BODY_STATUS, {
        "door_fl": False, "door_fr": True, "door_rl": False, "door_rr": False,
        "bonnet": False, "boot": False, "mirror_l": False, "mirror_r": False,
    })
    ingest(model, CanId.TYRE_PRESSURE, {
        "tyre_fl": 2.42, "tyre_fr": 2.40, "tyre_rl": 2.38, "tyre_rr": 2.41,
    })
    snapshot = model.snapshot()
    assert snapshot.link is True
    assert snapshot.speed_kmh == 87.4
    assert snapshot.rpm == 2850
    assert snapshot.gear == "D"
    assert snapshot.driving_mode == "SPORT"
    assert snapshot.left_indicator is True
    assert snapshot.doors["fr"] is True
    assert snapshot.tyre_pressure["fl"] == 2.42
    assert "DOOR OPEN" in snapshot.warnings
    assert snapshot.frames_total == 9


def test_model_reports_no_link_without_frames():
    model = VehicleModel()
    snapshot = model.snapshot()
    assert snapshot.link is False
    assert "NO CAN LINK" in snapshot.warnings


def test_model_marks_low_fuel_and_battery_warnings():
    model = VehicleModel()
    ingest(model, CanId.FUEL_LEVEL, {"fuel_level": 5.0})
    ingest(model, CanId.BATTERY_VOLTAGE, {"battery_voltage": 11.2})
    snapshot = model.snapshot()
    assert snapshot.fuel_low is True
    assert snapshot.battery_low is True
    assert "LOW FUEL" in snapshot.warnings
    assert "LOW BATTERY" in snapshot.warnings

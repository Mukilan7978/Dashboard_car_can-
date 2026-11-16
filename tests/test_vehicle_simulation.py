from __future__ import annotations

import time

from vehicle.vehicle_controller import VehicleController
from vehicle.vehicle_physics import VehiclePhysics
from vehicle.vehicle_state import VehicleState


def test_controller_changes_gear_mode_and_lights():
    state = VehicleState()
    controller = VehicleController(state)
    now = time.monotonic()
    controller.apply({"cmd": "set_gear", "value": "D"}, now)
    assert state.gear == "D"
    assert state.parking_brake is False
    controller.apply({"cmd": "mode_set", "value": "SPORT"}, now)
    assert state.driving_mode == "SPORT"
    controller.apply({"cmd": "steering_setting", "value": "SPORT"}, now)
    assert state.steering_setting == "SPORT"
    controller.apply({"cmd": "light_toggle", "value": "low_beam"}, now)
    assert state.lights["low_beam"] is True
    controller.apply({"cmd": "light_toggle", "value": "low_beam"}, now)
    assert state.lights["low_beam"] is False
    controller.apply({"cmd": "door_toggle", "value": "fr"}, now)
    assert state.doors["fr"] is True
    controller.apply({"cmd": "close_all"}, now)
    assert not any(state.doors.values())


def test_cannot_select_park_while_moving():
    state = VehicleState()
    state.speed_kmh = 40.0
    state.gear = "D"
    controller = VehicleController(state)
    controller.apply({"cmd": "set_gear", "value": "P"}, time.monotonic())
    assert state.gear == "D"
    assert state.speed_kmh == 40.0


def test_engine_starts_off_and_does_not_drive():
    state = VehicleState()
    state.gear = "D"
    state.throttle = 1.0
    state.parking_brake = False
    physics = VehiclePhysics()
    for _ in range(50):
        physics.step(state, 0.02)
    assert state.engine_on is False
    assert state.speed_kmh == 0.0
    assert state.rpm < 5.0


def test_engine_start_stop_commands():
    state = VehicleState()
    controller = VehicleController(state)
    now = time.monotonic()
    controller.apply({"cmd": "engine_start"}, now)
    assert state.engine_on is True
    controller.apply({"cmd": "engine_stop"}, now)
    assert state.engine_on is False
    controller.apply({"cmd": "engine_toggle"}, now)
    assert state.engine_on is True


def test_parking_brake_holds_vehicle():
    state = VehicleState()
    state.gear = "D"
    state.engine_on = True
    state.throttle = 1.0
    state.parking_brake = True
    physics = VehiclePhysics()
    for _ in range(50):
        physics.step(state, 0.02)
    assert state.speed_kmh == 0.0


def test_physics_accelerates_shifts_and_consumes_fuel():
    state = VehicleState()
    state.gear = "D"
    state.engine_on = True
    state.throttle = 1.0
    state.parking_brake = False
    start_fuel = state.fuel_percent
    physics = VehiclePhysics()
    for _ in range(250):
        physics.step(state, 0.02)
    assert state.speed_kmh > 35.0
    assert state.manual_gear >= 2
    assert state.fuel_percent < start_fuel
    assert state.rpm > 750.0
    assert state.trip_km > 0.0


def test_indicator_blink_toggles_over_time():
    state = VehicleState()
    state.left_indicator = True
    physics = VehiclePhysics()
    seen = set()
    deadline = time.monotonic() + 1.3
    while time.monotonic() < deadline:
        physics.step(state, 0.02)
        seen.add(state.active_left_indicator)
        if seen == {True, False}:
            break
        time.sleep(0.01)
    assert seen == {True, False}
    assert state.left_indicator is True
    assert state.active_right_indicator is False

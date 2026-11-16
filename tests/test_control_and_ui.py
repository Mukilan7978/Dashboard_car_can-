from __future__ import annotations

from pathlib import Path

from vehicle.control_protocol import decode_command, encode_command


def test_control_protocol_round_trip():
    command = {"cmd": "mode_set", "value": "SPORT PLUS"}
    raw = encode_command(command)
    assert decode_command(raw) == command
    assert decode_command(b"not json") is None
    assert decode_command(b"[]") is None


def test_cockpit_screen_renders(qapp):
    from dashboard.model import VehicleSnapshot
    from dashboard.screens.cockpit import CockpitScreen
    from dashboard.theme import get_theme, stylesheet

    theme = get_theme("COMFORT")
    qapp.setStyleSheet(stylesheet(theme))
    snapshot = VehicleSnapshot(
        link=True,
        speed_kmh=88.0,
        rpm=2850.0,
        engine_temp_c=92.0,
        fuel_percent=68.0,
        gear="D",
        manual_gear=3,
        driving_mode="COMFORT",
        battery_v=12.6,
        odometer_km=12450.3,
        trip_km=84.2,
        avg_consumption=8.1,
    )
    screen = CockpitScreen(theme)
    screen.resize(1600, 780)
    screen.set_snapshot(snapshot)
    screen.show()
    qapp.processEvents()
    pixmap = screen.grab()
    assert not pixmap.isNull()
    assert pixmap.width() == 1600
    assert pixmap.height() == 780
    screen.close()
    screen.deleteLater()
    qapp.processEvents()


def test_hidden_can_monitor_stops_terminal_work(qapp):
    import can

    from can_bus.can_decoder import decode_message
    from can_bus.message_ids import CanId
    from dashboard.theme import get_theme
    from monitor.monitor_widget import CanMonitorWidget

    monitor = CanMonitorWidget(get_theme("COMFORT"), "vcan0")
    frame = decode_message(
        can.Message(
            arbitration_id=CanId.VEHICLE_SPEED,
            data=bytes((0xE8, 0x03)),
            is_extended_id=False,
        )
    )
    monitor.append_frame(frame)
    assert len(monitor.pending) == 0

    monitor.set_active(True)
    monitor.append_frame(frame)
    assert len(monitor.pending) == 1
    monitor.set_active(False)
    assert len(monitor.pending) == 0
    monitor.close()
    monitor.deleteLater()
    qapp.processEvents()


def test_cockpit_engine_button_reflects_ignition(qapp):
    from dashboard.model import VehicleSnapshot
    from dashboard.theme import get_theme
    from dashboard.widgets.cluster_center import ClusterCenter

    center = ClusterCenter(get_theme("COMFORT"))
    center.set_snapshot(VehicleSnapshot(link=True, engine_running=False))
    assert center.start_button.text() == "START ENGINE"
    center.set_snapshot(VehicleSnapshot(link=True, engine_running=True))
    assert center.start_button.text() == "STOP ENGINE"
    center.close()
    center.deleteLater()
    qapp.processEvents()


def test_cockpit_scales_for_large_displays(qapp):
    from dashboard.screens.cockpit import CockpitScreen
    from dashboard.theme import get_theme

    screen = CockpitScreen(get_theme("COMFORT"))
    screen.resize(1600, 900)
    screen.show()
    qapp.processEvents()
    normal_metrics = screen.metrics.height()
    normal_button = screen.cluster_center.start_button.height()
    normal_roundel = screen.cluster_center.roundel.width()

    screen.resize(3840, 2160)
    qapp.processEvents()
    assert screen.metrics.height() > normal_metrics * 2
    assert screen.cluster_center.start_button.height() > normal_button * 2
    assert screen.cluster_center.roundel.width() > normal_roundel * 2

    screen.close()
    screen.deleteLater()
    qapp.processEvents()


def test_control_socket_path_is_isolated():
    from config.settings import RUNTIME_DIR

    assert isinstance(RUNTIME_DIR, Path)
    assert "automotive-dashboard" in str(RUNTIME_DIR)

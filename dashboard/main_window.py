from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import QEvent, QTimer, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QLineEdit,
    QMainWindow,
    QPlainTextEdit,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from can_bus.can_decoder import DecodedFrame
from config.settings import CONTROL_SOCKET
from monitor.monitor_widget import CanMonitorWidget
from .can_source import CanBusSource
from .control_client import ControlClient
from .model import VehicleModel, VehicleSnapshot
from .screens.cockpit import CockpitScreen
from .screens.energy import EnergyScreen
from .screens.media import MediaScreen
from .screens.navigation import NavigationScreen
from .screens.service import ServiceScreen
from .screens.settings import SettingsScreen
from .screens.vehicle import VehicleScreen
from .screens.tyre_pressure import TyrePressureScreen
from .screens.vehicle_body import VehicleBodyScreen
from .screens.lighting_control import LightingControlScreen
from .screens.driving_information import DrivingInformationScreen
from .screens.engine_information import EngineInformationScreen
from .screens.battery_information import BatteryInformationScreen
from .screens.vehicle_settings import VehicleSettingsScreen
from .theme import Theme, get_theme, stylesheet
from .widgets.header_footer import FooterBar, HeaderBar
from .widgets.toast import Toast


class MainWindow(QMainWindow):
    SCREEN_NAMES = (
        "Cockpit",
        "Vehicle",
        "Navigation",
        "Media",
        "Energy",
        "Service",
        "Settings",
        "Tyre Pressure",
        "Vehicle Body",
        "Lighting Control",
        "Driving Information",
        "Engine Information",
        "Battery Information",
        "Vehicle Settings",
    )
    MODES = ("ECO", "COMFORT", "SPORT", "SPORT PLUS")
    DRIVE_KEYS = frozenset((
        Qt.Key.Key_W, Qt.Key.Key_S, Qt.Key.Key_A, Qt.Key.Key_D,
        Qt.Key.Key_Up, Qt.Key.Key_Down, Qt.Key.Key_Left, Qt.Key.Key_Right,
        Qt.Key.Key_Space, Qt.Key.Key_H, Qt.Key.Key_E, Qt.Key.Key_K,
        Qt.Key.Key_G, Qt.Key.Key_V, Qt.Key.Key_B, Qt.Key.Key_M, Qt.Key.Key_N,
        Qt.Key.Key_Comma, Qt.Key.Key_Period, Qt.Key.Key_Shift,
    ))

    def __init__(
        self,
        channel: str = "vcan0",
        interface: str = "socketcan",
        control_socket: Path | str = CONTROL_SOCKET,
    ) -> None:
        super().__init__()
        self.channel = channel
        self.interface = interface
        self.theme: Theme = get_theme("COMFORT")
        self.model = VehicleModel(self)
        self._last_snapshot: VehicleSnapshot | None = None
        self._bus_open = False
        self._fullscreen = False
        self._monitor_visible = False
        self._shift_pressed = {"left": False, "right": False}
        self._shift_used = {"left": False, "right": False}
        self._steer_left = False
        self._steer_right = False
        self._held: set[str] = set()
        self._current_screen = 0
        self._tick_count = 0
        self._last_link: bool | None = None
        self._last_engine_running: bool | None = None
        self._last_gear: str | None = None

        self.setWindowTitle("AUTOSIM Cockpit — Automotive Dashboard Simulator")
        self.resize(1600, 900)
        self.setMinimumSize(1280, 720)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._build_ui()
        self._apply_theme(self.theme, force=True)

        self.control = ControlClient(control_socket)
        self.control.start()

        self.source = CanBusSource(channel, interface, self)
        self.source.frame_received.connect(self._on_frame)
        self.source.link_changed.connect(self._on_link)
        self.source.start()

        app = QApplication.instance()
        if app is not None:
            app.installEventFilter(self)

        self.timer = QTimer(self)
        self.timer.setInterval(33)  # ~30 updates per second for smooth RPM/speed
        self.timer.timeout.connect(self._tick)
        self.timer.start()

        self.heartbeat = QTimer(self)
        self.heartbeat.setInterval(500)
        self.heartbeat.timeout.connect(self._send_heartbeat)
        self.heartbeat.start()
        self._tick()

    def _build_ui(self) -> None:
        central = QWidget()
        central.setObjectName("Root")
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.header = HeaderBar(self.theme, self.channel)
        self.stack = QStackedWidget()
        self.cockpit_screen = CockpitScreen(self.theme)
        self.vehicle_screen = VehicleScreen(self.theme)
        self.navigation_screen = NavigationScreen(self.theme)
        self.media_screen = MediaScreen(self.theme)
        self.energy_screen = EnergyScreen(self.theme)
        self.service_screen = ServiceScreen(self.theme)
        self.settings_screen = SettingsScreen(self.theme)
        self.tyre_pressure_screen = TyrePressureScreen(self.theme)
        self.vehicle_body_screen = VehicleBodyScreen(self.theme)
        self.lighting_control_screen = LightingControlScreen(self.theme)
        self.driving_information_screen = DrivingInformationScreen(self.theme)
        self.engine_information_screen = EngineInformationScreen(self.theme)
        self.battery_information_screen = BatteryInformationScreen(self.theme)
        self.vehicle_settings_screen = VehicleSettingsScreen(self.theme)
        self.screens = [
            self.cockpit_screen,
            self.vehicle_screen,
            self.navigation_screen,
            self.media_screen,
            self.energy_screen,
            self.service_screen,
            self.settings_screen,
            self.tyre_pressure_screen,
            self.vehicle_body_screen,
            self.lighting_control_screen,
            self.driving_information_screen,
            self.engine_information_screen,
            self.battery_information_screen,
            self.vehicle_settings_screen,
        ]
        for screen in self.screens:
            screen.command_requested.connect(self._send_command)
            self.stack.addWidget(screen)
        self.footer = FooterBar(self.theme)

        layout.addWidget(self.header, 0)
        layout.addWidget(self.stack, 1)
        layout.addWidget(self.footer, 0)
        self.setCentralWidget(central)

        self.overlay = QFrame(central)
        self.overlay.setObjectName("Root")
        overlay_layout = QVBoxLayout(self.overlay)
        overlay_layout.setContentsMargins(0, 0, 0, 0)
        overlay_layout.setSpacing(0)
        self.monitor = CanMonitorWidget(self.theme, self.channel)
        self.monitor.close_requested.connect(self.hide_monitor)
        overlay_layout.addWidget(self.monitor)
        self.overlay.hide()

        self.toast = Toast(central)

    def _apply_theme(self, theme: Theme, force: bool = False) -> None:
        if not force and theme.name == self.theme.name:
            return
        self.theme = theme
        self.setStyleSheet(stylesheet(theme))
        self.header.set_theme(theme)
        self.footer.set_theme(theme)
        for screen in self.screens:
            screen.set_theme(theme)
        self.monitor.set_theme(theme)
        if self._last_snapshot is not None:
            self._refresh_current(self._last_snapshot)

    def _tick(self) -> None:
        self._tick_count += 1
        snapshot = self.model.snapshot()
        # Only refresh if snapshot data has changed significantly
        if self._last_snapshot is None:
            self._last_snapshot = snapshot
            self._refresh_current(snapshot)
            self._apply_theme(get_theme(snapshot.driving_mode))
            self._announce_state(snapshot)
            return
        
        # Check if any relevant values changed
        changed = (
            snapshot.speed_kmh != self._last_snapshot.speed_kmh or
            snapshot.rpm != self._last_snapshot.rpm or
            snapshot.gear != self._last_snapshot.gear or
            snapshot.engine_running != self._last_snapshot.engine_running or
            snapshot.link != self._last_snapshot.link
        )
        
        if changed or self._tick_count % 6 == 0:
            self._last_snapshot = snapshot
            self._refresh_current(snapshot)
            self._apply_theme(get_theme(snapshot.driving_mode))
        
        self._announce_state(snapshot)

    def _refresh_current(self, snapshot: VehicleSnapshot) -> None:
        screen = self.stack.currentWidget()
        if screen is not None:
            screen.set_snapshot(snapshot)

    def _on_frame(self, frame: DecodedFrame) -> None:
        self.model.ingest(frame)
        self.monitor.append_frame(frame)

    def _on_link(self, link: bool, text: str) -> None:
        self._bus_open = link
        self.monitor.set_link(link, self.channel if link else text)

    def _send_command(self, command: dict[str, Any]) -> None:
        self.control.send(command)

    def _send_heartbeat(self) -> None:
        self.control.send({"cmd": "heartbeat"})

    def _send_input(self, name: str, value: Any) -> None:
        self.control.send({"cmd": "input", "name": name, "value": value})

    def _switch_screen(self, index: int) -> None:
        if not 0 <= index < len(self.screens):
            return
        if self._monitor_visible:
            self.hide_monitor()
        self._current_screen = index
        self.stack.setCurrentIndex(index)
        name = self.SCREEN_NAMES[index]
        self.setWindowTitle(
            f"AUTOSIM Cockpit — {name} — Automotive Dashboard Simulator"
        )
        if self._last_snapshot is not None:
            self._refresh_current(self._last_snapshot)
        self.setFocus()

    def show_monitor(self) -> None:
        self._monitor_visible = True
        self.overlay.setGeometry(self.centralWidget().rect())
        self.overlay.show()
        self.overlay.raise_()
        self.monitor.set_active(True)
        self.monitor.setFocus()

    def hide_monitor(self) -> None:
        self._monitor_visible = False
        self.monitor.set_active(False)
        self.overlay.hide()
        self.setFocus()

    def toggle_monitor(self) -> None:
        if self._monitor_visible:
            self.hide_monitor()
        else:
            self.show_monitor()

    def toggle_fullscreen(self) -> None:
        self._fullscreen = not self._fullscreen
        if self._fullscreen:
            self.showFullScreen()
        else:
            self.showNormal()

    def _mode_cycle(self) -> None:
        current = self._last_snapshot.driving_mode if self._last_snapshot else "COMFORT"
        try:
            index = self.MODES.index(current)
        except ValueError:
            index = 1
        self._send_command({"cmd": "mode_set", "value": self.MODES[(index + 1) % len(self.MODES)]})

    def _steering_toggle(self) -> None:
        current = (
            self._last_snapshot.steering_setting if self._last_snapshot else "COMFORT"
        )
        value = "SPORT" if current == "COMFORT" else "COMFORT"
        self._send_command({"cmd": "steering_setting", "value": value})

    def _update_steering(self) -> None:
        value = 0.0
        if self._steer_left:
            value -= 1.0
        if self._steer_right:
            value += 1.0
        self._send_input("steering", value)

    def _release_controls(self) -> None:
        for name in ("throttle", "brake", "emergency_brake", "horn"):
            if name in self._held:
                self._send_input(name, False)
        self._held.clear()
        if self._steer_left or self._steer_right:
            self._steer_left = False
            self._steer_right = False
            self._update_steering()
        self._shift_pressed = {"left": False, "right": False}
        self._shift_used = {"left": False, "right": False}

    def show_toast(self, text: str, level: str = "info") -> None:
        self.toast.show_message(text, level, self.theme)

    def _announce_state(self, snapshot: VehicleSnapshot) -> None:
        if self._last_engine_running is None:
            self._last_engine_running = snapshot.engine_running
            self._last_gear = snapshot.gear
            return
        if snapshot.engine_running != self._last_engine_running:
            self._last_engine_running = snapshot.engine_running
            self.show_toast(
                "ENGINE STARTED" if snapshot.engine_running else "ENGINE STOPPED",
                "ok" if snapshot.engine_running else "warn",
            )
        if snapshot.link and snapshot.gear != self._last_gear:
            self._last_gear = snapshot.gear
            self.show_toast(f"GEAR  {snapshot.gear_text}", "info")

    def _shift_side(self, event: QKeyEvent) -> str:
        scan = int(event.nativeScanCode())
        if scan == 50:
            return "left"
        if scan == 62:
            return "right"
        virtual = int(event.nativeVirtualKey())
        if virtual == 0xFFE1:
            return "left"
        if virtual == 0xFFE2:
            return "right"
        if self._shift_pressed["left"] and not self._shift_pressed["right"]:
            return "left"
        if self._shift_pressed["right"] and not self._shift_pressed["left"]:
            return "right"
        return "left"

    def _text_input_focused(self) -> bool:
        focus = QApplication.focusWidget()
        return isinstance(focus, (QLineEdit, QTextEdit, QPlainTextEdit))

    def eventFilter(self, obj: object, event: QEvent) -> bool:
        if event.type() == QEvent.Type.WindowDeactivate:
            self._release_controls()
            return super().eventFilter(obj, event)
        if event.type() not in (QEvent.Type.KeyPress, QEvent.Type.KeyRelease):
            return super().eventFilter(obj, event)
        key_event = event
        if not isinstance(key_event, QKeyEvent):
            return super().eventFilter(obj, event)
        key = key_event.key()
        modifiers = key_event.modifiers()
        control = bool(modifiers & Qt.KeyboardModifier.ControlModifier)

        if self._monitor_visible:
            if key_event.type() == QEvent.Type.KeyPress:
                if key == Qt.Key.Key_F12:
                    self.hide_monitor()
                    return True
                if key == Qt.Key.Key_Escape:
                    self.hide_monitor()
                    return True
        if Qt.Key.Key_F1 <= key <= Qt.Key.Key_F7:
            self._switch_screen(key - Qt.Key.Key_F1)
            return True

        if self._text_input_focused():
            return super().eventFilter(obj, event)

        if key_event.isAutoRepeat():
            if key in self.DRIVE_KEYS or Qt.Key.Key_F1 <= key <= Qt.Key.Key_F7:
                return True

        if key_event.type() == QEvent.Type.KeyPress:
            if Qt.Key.Key_F1 <= key <= Qt.Key.Key_F7:
                self._switch_screen(key - Qt.Key.Key_F1)
                return True
            if control and Qt.Key.Key_1 <= key <= Qt.Key.Key_7:
                self._switch_screen(key - Qt.Key.Key_1)
                return True
            if key == Qt.Key.Key_F11:
                self.toggle_fullscreen()
                return True
            if key == Qt.Key.Key_F12:
                self.show_monitor()
                return True
            if key == Qt.Key.Key_Escape:
                if self._fullscreen:
                    self.toggle_fullscreen()
                    return True
                return False

            for side in ("left", "right"):
                if self._shift_pressed[side]:
                    self._shift_used[side] = True

            if key == Qt.Key.Key_Shift:
                side = self._shift_side(key_event)
                self._shift_pressed[side] = True
                self._shift_used[side] = False
                return True

            if key in (Qt.Key.Key_Comma, Qt.Key.Key_Period):
                side = "left" if key == Qt.Key.Key_Comma else "right"
                self._send_command({"cmd": "indicator", "value": side})
                return True
            if key == Qt.Key.Key_G:
                self._send_command({"cmd": "gear_cycle_mode"})
                return True
            if key == Qt.Key.Key_M:
                if self._last_snapshot and self._last_snapshot.gear == "M":
                    self._send_command({"cmd": "gear_next"})
                return True
            if key == Qt.Key.Key_N:
                if self._last_snapshot and self._last_snapshot.gear == "M":
                    self._send_command({"cmd": "gear_prev"})
                return True
            if key == Qt.Key.Key_V:
                self._mode_cycle()
                return True
            if key == Qt.Key.Key_B:
                self._steering_toggle()
                return True
            if key == Qt.Key.Key_E:
                self._send_command({"cmd": "engine_toggle"})
                return True
            if key == Qt.Key.Key_K:
                self._send_command({"cmd": "parking_brake_toggle"})
                return True
            if key in (Qt.Key.Key_W, Qt.Key.Key_Up):
                if "throttle" not in self._held:
                    self._held.add("throttle")
                    self._send_input("throttle", True)
                return True
            if key in (Qt.Key.Key_S, Qt.Key.Key_Down):
                if "brake" not in self._held:
                    self._held.add("brake")
                    self._send_input("brake", True)
                return True
            if key in (Qt.Key.Key_A, Qt.Key.Key_Left):
                self._steer_left = True
                self._update_steering()
                return True
            if key in (Qt.Key.Key_D, Qt.Key.Key_Right):
                self._steer_right = True
                self._update_steering()
                return True
            if key == Qt.Key.Key_Space:
                if "emergency" not in self._held:
                    self._held.add("emergency")
                    self._send_input("emergency_brake", True)
                return True
            if key == Qt.Key.Key_H:
                if "horn" not in self._held:
                    self._held.add("horn")
                    self._send_input("horn", True)
                return True

        if key_event.type() == QEvent.Type.KeyRelease:
            if key == Qt.Key.Key_Shift:
                side = self._shift_side(key_event)
                if self._shift_pressed[side] and not self._shift_used[side]:
                    self._send_command({"cmd": "indicator", "value": side})
                self._shift_pressed[side] = False
                self._shift_used[side] = False
                return True
            if key in (Qt.Key.Key_W, Qt.Key.Key_Up):
                if "throttle" in self._held:
                    self._held.discard("throttle")
                    self._send_input("throttle", False)
                return True
            if key in (Qt.Key.Key_S, Qt.Key.Key_Down):
                if "brake" in self._held:
                    self._held.discard("brake")
                    self._send_input("brake", False)
                return True
            if key in (Qt.Key.Key_A, Qt.Key.Key_Left):
                self._steer_left = False
                self._update_steering()
                return True
            if key in (Qt.Key.Key_D, Qt.Key.Key_Right):
                self._steer_right = False
                self._update_steering()
                return True
            if key == Qt.Key.Key_Space:
                if "emergency" in self._held:
                    self._held.discard("emergency")
                    self._send_input("emergency_brake", False)
                return True
            if key == Qt.Key.Key_H:
                if "horn" in self._held:
                    self._held.discard("horn")
                    self._send_input("horn", False)
                return True

        return super().eventFilter(obj, event)

    def resizeEvent(self, event: object) -> None:
        super().resizeEvent(event)
        if hasattr(self, "header"):
            scale = max(
                0.78,
                min(2.6, min(self.width() / 1600.0, self.height() / 900.0)),
            )
            self.header.setFixedHeight(max(52, round(66 * scale)))
            self.footer.setFixedHeight(max(32, round(40 * scale)))
        if hasattr(self, "overlay"):
            self.overlay.setGeometry(self.centralWidget().rect())
        if hasattr(self, "toast") and self.toast.isVisible():
            self.toast._reposition()

    def closeEvent(self, event: object) -> None:
        app = QApplication.instance()
        if app is not None:
            app.removeEventFilter(self)
        self.timer.stop()
        self.heartbeat.stop()
        self._release_controls()
        self.source.stop()
        self.source.wait(1500)
        self.control.stop()
        super().closeEvent(event)

from __future__ import annotations

from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from dashboard.theme import Theme
from dashboard.widgets.card import Card
from dashboard.widgets.status_list import StatusList
from .base import BaseScreen


class SettingsScreen(BaseScreen):
    MODES = ("ECO", "COMFORT", "SPORT", "SPORT PLUS")
    STEERING = ("COMFORT", "SPORT")
    DOORS = (("fl", "FL"), ("fr", "FR"), ("rl", "RL"), ("rr", "RR"))
    LIGHTS = (
        ("low_beam", "LOW BEAM"),
        ("high_beam", "HIGH BEAM"),
        ("drl", "DRL"),
        ("fog", "FOG"),
    )

    def __init__(self, theme: Theme) -> None:
        super().__init__(theme)
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 14, 18, 14)
        root.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setStyleSheet(
            "QScrollArea, QScrollArea > QWidget > QWidget "
            "{ background: transparent; }"
        )
        content = QWidget()
        grid = QGridLayout(content)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(10)
        scroll.setWidget(content)
        root.addWidget(scroll)

        driving_card = Card(theme, "Driving dynamics", "mode")
        mode_label = QLabel("DRIVING MODE")
        mode_label.setObjectName("CardTitle")
        driving_card.body.addWidget(mode_label)
        mode_grid = QGridLayout()
        mode_grid.setSpacing(6)
        self.mode_buttons: dict[str, QPushButton] = {}
        for index, mode in enumerate(self.MODES):
            button = QPushButton(mode)
            button.setCheckable(True)
            button.clicked.connect(
                lambda _checked=False, value=mode: self.send(
                    "mode_set", value=value
                )
            )
            mode_grid.addWidget(button, index // 2, index % 2)
            self.mode_buttons[mode] = button
        driving_card.body.addLayout(mode_grid)

        steering_label = QLabel("STEERING WEIGHT")
        steering_label.setObjectName("CardTitle")
        driving_card.body.addWidget(steering_label)
        steering_row = QHBoxLayout()
        steering_row.setSpacing(6)
        self.steering_buttons: dict[str, QPushButton] = {}
        for value in self.STEERING:
            button = QPushButton(value)
            button.setCheckable(True)
            button.clicked.connect(
                lambda _checked=False, mode=value: self.send(
                    "steering_setting", value=mode
                )
            )
            steering_row.addWidget(button)
            self.steering_buttons[value] = button
        driving_card.body.addLayout(steering_row)

        driving_actions = QGridLayout()
        driving_actions.setSpacing(6)
        for index, (label, command) in enumerate((
            ("ENGINE ON/OFF", "engine_toggle"),
            ("PARK BRAKE", "parking_brake_toggle"),
            ("SEATBELT", "seatbelt_toggle"),
            ("RESET TRIP", "trip_reset"),
        )):
            button = QPushButton(label)
            button.clicked.connect(
                lambda _checked=False, name=command: self.send(name)
            )
            driving_actions.addWidget(button, index // 2, index % 2)
        driving_card.body.addLayout(driving_actions)
        driving_card.body.addStretch(1)
        grid.addWidget(driving_card, 0, 0)

        lighting_card = Card(theme, "Lighting and signals", "low_beam")
        light_grid = QGridLayout()
        light_grid.setSpacing(6)
        for index, (key, label) in enumerate(self.LIGHTS):
            button = QPushButton(label)
            button.clicked.connect(
                lambda _checked=False, light=key: self.send(
                    "light_toggle", value=light
                )
            )
            light_grid.addWidget(button, index // 2, index % 2)
        lighting_card.body.addLayout(light_grid)
        indicator_row = QHBoxLayout()
        indicator_row.setSpacing(6)
        for label, command, value in (
            ("LEFT", "indicator", "left"),
            ("RIGHT", "indicator", "right"),
            ("OFF", "indicator", "off"),
            ("HAZARD", "hazard_toggle", None),
        ):
            button = QPushButton(label)
            if value is None:
                button.clicked.connect(
                    lambda _checked=False, name=command: self.send(name)
                )
            else:
                button.clicked.connect(
                    lambda _checked=False, name=command, val=value: self.send(
                        name, value=val
                    )
                )
            indicator_row.addWidget(button)
        lighting_card.body.addLayout(indicator_row)
        all_off = QPushButton("ALL LIGHTS OFF")
        all_off.clicked.connect(lambda: self.send("all_lights_off"))
        lighting_card.body.addWidget(all_off)
        lighting_card.body.addStretch(1)
        grid.addWidget(lighting_card, 0, 1)

        body_card = Card(theme, "Body controls", "door")
        door_row = QHBoxLayout()
        door_row.setSpacing(6)
        for key, label in self.DOORS:
            button = QPushButton(label)
            button.clicked.connect(
                lambda _checked=False, value=key: self.send(
                    "door_toggle", value=value
                )
            )
            door_row.addWidget(button)
        body_card.body.addLayout(door_row)
        body_actions = QGridLayout()
        body_actions.setSpacing(6)
        for index, (label, command) in enumerate((
            ("BONNET", "bonnet_toggle"),
            ("BOOT", "boot_toggle"),
            ("MIRROR L", "mirror_toggle"),
            ("MIRROR R", "mirror_toggle"),
        )):
            button = QPushButton(label)
            if command == "mirror_toggle":
                side = "l" if "L" in label else "r"
                button.clicked.connect(
                    lambda _checked=False, name=command, value=side: self.send(
                        name, value=value
                    )
                )
            else:
                button.clicked.connect(
                    lambda _checked=False, name=command: self.send(name)
                )
            body_actions.addWidget(button, index // 2, index % 2)
        body_card.body.addLayout(body_actions)
        close_all = QPushButton("CLOSE ALL")
        close_all.clicked.connect(lambda: self.send("close_all"))
        body_card.body.addWidget(close_all)
        body_card.body.addStretch(1)
        grid.addWidget(body_card, 1, 0)

        diagnostics = Card(theme, "CAN diagnostics", "monitor")
        self.diag_list = StatusList(theme, 7)
        self.diag_list.set_items([
            ("link", "Bus link"),
            ("channel", "Channel"),
            ("control", "Control socket"),
            ("frames", "Frames received"),
            ("invalid", "Invalid frames"),
            ("rate", "Receive rate"),
            ("source", "Data source"),
        ])
        diagnostics.body.addWidget(self.diag_list)
        grid.addWidget(diagnostics, 1, 1)

        help_card = Card(theme, "Keyboard controls", "settings")
        help_text = QLabel(
            "F1 – F7  ·  switch screens\n"
            "Ctrl + 1 – 7  ·  switch screens\n"
            "G  ·  cycle P / R / N / D / M\n"
            "M  ·  manual gear up (in M)\n"
            "N  ·  manual gear down (in M)\n"
            "V  ·  cycle driving mode\n"
            "B  ·  toggle steering weight\n"
            "W / Up  ·  throttle     S / Down  ·  brake\n"
            "A / D  ·  steer left / right\n"
            "Left Shift / Right Shift  ·  indicators\n"
            ", / .  ·  indicator fallback\n"
            "Space  ·  emergency brake     H  ·  horn\n"
            "E  ·  engine toggle     K  ·  parking brake\n"
            "F11  ·  fullscreen     F12  ·  CAN monitor\n"
            "Esc  ·  close monitor / leave fullscreen"
        )
        help_text.setObjectName("Subtle")
        help_text.setWordWrap(True)
        help_text.setStyleSheet("line-height: 1.55; font-size: 11px;")
        help_card.body.addWidget(help_text)
        help_card.body.addStretch(1)
        grid.addWidget(help_card, 2, 0, 1, 2)
        grid.setRowStretch(0, 0)
        grid.setRowStretch(1, 0)
        grid.setRowStretch(2, 0)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        self.channel = "vcan0"
        self.control_connected = False

    def set_diagnostics(self, channel: str, control_connected: bool) -> None:
        self.channel = channel
        self.control_connected = control_connected

    def refresh(self) -> None:
        snapshot = self.snapshot
        if snapshot is None:
            return
        for mode, button in self.mode_buttons.items():
            button.blockSignals(True)
            button.setChecked(mode == snapshot.driving_mode)
            button.blockSignals(False)
        for value, button in self.steering_buttons.items():
            button.blockSignals(True)
            button.setChecked(value == snapshot.steering_setting)
            button.blockSignals(False)

        self.diag_list.set_value(
            "link", "ONLINE" if snapshot.link else "OFFLINE",
            "ok" if snapshot.link else "bad",
        )
        self.diag_list.set_value("channel", self.channel, "info")
        self.diag_list.set_value(
            "control", "CONNECTED" if self.control_connected else "OFFLINE",
            "ok" if self.control_connected else "warn",
        )
        self.diag_list.set_value("frames", f"{snapshot.frames_total}", "info")
        self.diag_list.set_value(
            "invalid", f"{snapshot.invalid_total}",
            "warn" if snapshot.invalid_total else "ok",
        )
        self.diag_list.set_value("rate", f"{snapshot.rx_rate:.0f} f/s", "info")
        self.diag_list.set_value("source", "SocketCAN / CAN frames", "info")

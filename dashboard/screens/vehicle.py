from __future__ import annotations

from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from config.settings import TYRE_HIGH_BAR, TYRE_LOW_BAR
from dashboard.theme import Theme
from dashboard.widgets.card import Card, MetricCard
from dashboard.widgets.status_list import StatusList
from dashboard.widgets.vehicle_display import VehicleDisplay
from .base import BaseScreen


class VehicleScreen(BaseScreen):
    TYRES = (
        ("fl", "Front left"),
        ("fr", "Front right"),
        ("rl", "Rear left"),
        ("rr", "Rear right"),
    )

    def __init__(self, theme: Theme) -> None:
        super().__init__(theme)
        root = QHBoxLayout(self)
        root.setContentsMargins(18, 14, 18, 14)
        root.setSpacing(12)

        self.car_card = Card(theme, "Vehicle status", "car")
        self.car_display = VehicleDisplay(theme)
        self.car_card.body.addWidget(self.car_display, 1)
        root.addWidget(self.car_card, 4)

        right = QVBoxLayout()
        right.setSpacing(10)

        tyre_grid = QGridLayout()
        tyre_grid.setSpacing(8)
        self.tyre_cards: dict[str, MetricCard] = {}
        for index, (key, label) in enumerate(self.TYRES):
            card = MetricCard(theme, label, "bar", "tyre", "—")
            tyre_grid.addWidget(card, index // 2, index % 2)
            self.tyre_cards[key] = card
        right.addLayout(tyre_grid, 0)

        lower = QHBoxLayout()
        lower.setSpacing(10)

        doors_card = Card(theme, "Doors", "door")
        self.doors_list = StatusList(theme, 4)
        self.doors_list.set_items([
            ("fl", "Front left"),
            ("fr", "Front right"),
            ("rl", "Rear left"),
            ("rr", "Rear right"),
        ])
        doors_card.body.addWidget(self.doors_list)
        door_buttons = QGridLayout()
        door_buttons.setSpacing(6)
        for index, key in enumerate(("fl", "fr", "rl", "rr")):
            button = QPushButton(key.upper())
            button.setFixedHeight(30)
            button.clicked.connect(
                lambda _checked=False, door=key: self.send("door_toggle", value=door)
            )
            door_buttons.addWidget(button, index // 2, index % 2)
        doors_card.body.addLayout(door_buttons)
        close_all = QPushButton("CLOSE ALL")
        close_all.setFixedHeight(30)
        close_all.clicked.connect(lambda: self.send("close_all"))
        doors_card.body.addWidget(close_all)
        doors_card.body.addStretch(1)
        lower.addWidget(doors_card, 1)

        lights_card = Card(theme, "Lighting", "low_beam")
        self.lights_list = StatusList(theme, 5)
        self.lights_list.set_items([
            ("low_beam", "Low beam"),
            ("high_beam", "High beam"),
            ("drl", "Daytime running"),
            ("fog", "Fog lamps"),
            ("reverse_light", "Reverse lamp"),
        ])
        lights_card.body.addWidget(self.lights_list)
        light_buttons = QGridLayout()
        light_buttons.setSpacing(6)
        for index, (key, label) in enumerate((
            ("low_beam", "LOW"),
            ("high_beam", "HIGH"),
            ("drl", "DRL"),
            ("fog", "FOG"),
        )):
            button = QPushButton(label)
            button.setFixedHeight(30)
            button.clicked.connect(
                lambda _checked=False, light=key: self.send("light_toggle", value=light)
            )
            light_buttons.addWidget(button, index // 2, index % 2)
        lights_card.body.addLayout(light_buttons)
        all_off = QPushButton("ALL LIGHTS OFF")
        all_off.setFixedHeight(30)
        all_off.clicked.connect(lambda: self.send("all_lights_off"))
        lights_card.body.addWidget(all_off)
        lights_card.body.addStretch(1)
        lower.addWidget(lights_card, 1)

        body_card = Card(theme, "Body and cabin", "seatbelt")
        self.body_list = StatusList(theme, 6)
        self.body_list.set_items([
            ("bonnet", "Bonnet"),
            ("boot", "Boot"),
            ("mirror_l", "Mirror left"),
            ("mirror_r", "Mirror right"),
            ("seatbelt", "Seatbelt"),
            ("parking_brake", "Parking brake"),
        ])
        body_card.body.addWidget(self.body_list)
        body_buttons = QHBoxLayout()
        body_buttons.setSpacing(6)
        bonnet = QPushButton("BONNET")
        bonnet.clicked.connect(lambda: self.send("bonnet_toggle"))
        boot = QPushButton("BOOT")
        boot.clicked.connect(lambda: self.send("boot_toggle"))
        body_buttons.addWidget(bonnet)
        body_buttons.addWidget(boot)
        body_card.body.addLayout(body_buttons)
        hazard = QPushButton("HAZARD")
        hazard.clicked.connect(lambda: self.send("hazard_toggle"))
        body_card.body.addWidget(hazard)
        body_card.body.addStretch(1)
        lower.addWidget(body_card, 1)

        right.addLayout(lower, 1)
        root.addLayout(right, 7)

    def refresh(self) -> None:
        snapshot = self.snapshot
        if snapshot is None:
            return
        self.car_display.set_snapshot(snapshot)

        for key, _label in self.TYRES:
            pressure = snapshot.tyre_pressure.get(key, 0.0)
            temp = snapshot.tyre_temp.get(key, 0.0)
            card = self.tyre_cards[key]
            if pressure <= 0:
                card.set_value("—", detail="No CAN data")
                card.set_tint(None)
            else:
                card.set_value(f"{pressure:.2f}", detail=f"{temp:.0f} °C")
                if pressure < TYRE_LOW_BAR or pressure > TYRE_HIGH_BAR:
                    card.set_tint(self.theme.red)
                else:
                    card.set_tint(None)

        for key, _label in self.TYRES:
            open_door = snapshot.doors.get(key, False)
            self.doors_list.set_value(
                key, "OPEN" if open_door else "CLOSED",
                "warn" if open_door else "ok",
            )

        light_values = (
            ("low_beam", snapshot.low_beam),
            ("high_beam", snapshot.high_beam),
            ("drl", snapshot.drl),
            ("fog", snapshot.fog),
            ("reverse_light", snapshot.reverse_light),
        )
        for key, active in light_values:
            self.lights_list.set_value(
                key, "ON" if active else "OFF",
                "info" if active else "off",
            )

        body_values = (
            ("bonnet", snapshot.bonnet, "OPEN", "CLOSED"),
            ("boot", snapshot.boot, "OPEN", "CLOSED"),
            ("mirror_l", snapshot.mirror_l, "FOLDED", "EXTENDED"),
            ("mirror_r", snapshot.mirror_r, "FOLDED", "EXTENDED"),
            ("seatbelt", snapshot.seatbelt, "FASTENED", "UNFASTENED"),
            ("parking_brake", snapshot.parking_brake, "ENGAGED", "RELEASED"),
        )
        for key, active, on_text, off_text in body_values:
            self.body_list.set_value(
                key, on_text if active else off_text,
                "warn" if active and key not in ("seatbelt",) else "ok",
            )
        self.body_list.set_value(
            "seatbelt", "FASTENED" if snapshot.seatbelt else "UNFASTENED",
            "ok" if snapshot.seatbelt else "bad",
        )

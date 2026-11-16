from __future__ import annotations

import time

from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
)

from config.settings import TYRE_HIGH_BAR, TYRE_LOW_BAR
from dashboard.theme import Theme
from dashboard.widgets.card import Card, MetricCard
from dashboard.widgets.history_chart import HistoryChart
from dashboard.widgets.status_list import StatusList
from .base import BaseScreen


class ServiceScreen(BaseScreen):
    def __init__(self, theme: Theme) -> None:
        super().__init__(theme)
        root = QHBoxLayout(self)
        root.setContentsMargins(18, 14, 18, 14)
        root.setSpacing(12)

        left = QVBoxLayout()
        left.setSpacing(10)
        warning_card = Card(theme, "Active warnings", "warning")
        self.warning_list = QListWidget()
        self.warning_list.setSelectionMode(
            QListWidget.SelectionMode.NoSelection
        )
        warning_card.body.addWidget(self.warning_list, 1)
        left.addWidget(warning_card, 1)

        health_card = Card(theme, "ECU and bus health", "monitor")
        self.health_list = StatusList(theme, 5)
        self.health_list.set_items([
            ("link", "CAN link"),
            ("engine", "Engine ECU"),
            ("transmission", "Transmission ECU"),
            ("body", "Body ECU"),
            ("gateway", "Gateway"),
        ])
        health_card.body.addWidget(self.health_list)
        left.addWidget(health_card, 0)

        actions = Card(theme, "Service actions", "settings")
        action_row = QHBoxLayout()
        action_row.setSpacing(6)
        for label, command in (
            ("ENGINE", "engine_toggle"),
            ("PARK BRAKE", "parking_brake_toggle"),
            ("SEATBELT", "seatbelt_toggle"),
        ):
            button = QPushButton(label)
            button.clicked.connect(
                lambda _checked=False, name=command: self.send(name)
            )
            action_row.addWidget(button)
        actions.body.addLayout(action_row)
        reset = QPushButton("RESET TRIP")
        reset.clicked.connect(lambda: self.send("trip_reset"))
        actions.body.addWidget(reset)
        left.addWidget(actions, 0)
        root.addLayout(left, 4)

        right = QVBoxLayout()
        right.setSpacing(10)
        metrics = QHBoxLayout()
        metrics.setSpacing(8)
        self.temp_card = MetricCard(theme, "Engine temperature", "°C", "temperature")
        self.battery_card = MetricCard(theme, "Battery", "V", "battery")
        self.oil_card = MetricCard(theme, "Oil pressure", "", "oil")
        self.engine_card = MetricCard(theme, "Engine status", "", "engine")
        for card in (
            self.temp_card,
            self.battery_card,
            self.oil_card,
            self.engine_card,
        ):
            metrics.addWidget(card, 1)
        right.addLayout(metrics, 0)

        chart_card = Card(theme, "Engine temperature history", "temperature")
        self.temp_chart = HistoryChart(
            theme, "Coolant temperature", "°C", 0, 140
        )
        chart_card.body.addWidget(self.temp_chart, 1)
        right.addWidget(chart_card, 1)

        tyres_card = Card(theme, "Tyre monitor", "tyre")
        self.tyre_list = StatusList(theme, 4)
        self.tyre_list.set_items([
            ("fl", "Front left"),
            ("fr", "Front right"),
            ("rl", "Rear left"),
            ("rr", "Rear right"),
        ])
        tyres_card.body.addWidget(self.tyre_list)
        right.addWidget(tyres_card, 0)
        root.addLayout(right, 7)

        self._last_sample = 0.0
        self._warning_cache: tuple[str, ...] = ()

    def refresh(self) -> None:
        snapshot = self.snapshot
        if snapshot is None:
            return
        self.temp_card.set_value(
            f"{snapshot.engine_temp_c:.0f}",
            detail="Warning at 110 °C" if snapshot.engine_temp_c < 110 else "OVERHEAT",
        )
        self.temp_card.set_tint(
            self.theme.red if snapshot.engine_temp_c >= 110 else None
        )
        self.battery_card.set_value(
            f"{snapshot.battery_v:.2f}",
            detail="Charging system" if snapshot.battery_v >= 11.8 else "LOW VOLTAGE",
        )
        self.battery_card.set_tint(
            self.theme.red if snapshot.battery_v < 11.8 else None
        )
        oil_ok = not snapshot.oil_pressure_warning
        self.oil_card.set_value(
            "OK" if oil_ok else "WARN",
            detail="Oil pressure switch" if snapshot.link else "No CAN link",
        )
        self.oil_card.set_tint(None if oil_ok else self.theme.red)
        engine_ok = snapshot.engine_running and not snapshot.check_engine
        self.engine_card.set_value(
            "RUNNING" if snapshot.engine_running else "STOPPED",
            detail="Check engine" if snapshot.check_engine else "No fault",
        )
        self.engine_card.set_tint(
            self.theme.red if snapshot.check_engine else None
        )

        warnings = snapshot.warnings or ["No active warnings"]
        key = tuple(warnings)
        if key != self._warning_cache:
            self._warning_cache = key
            self.warning_list.clear()
            for warning in warnings:
                item = QListWidgetItem(warning)
                if warning == "No active warnings":
                    item.setForeground(QColor(self.theme.green))
                elif warning in ("NO CAN LINK", "LOW BATTERY", "ENGINE HOT"):
                    item.setForeground(QColor(self.theme.red))
                else:
                    item.setForeground(QColor(self.theme.amber))
                self.warning_list.addItem(item)

        self.health_list.set_value(
            "link", "ONLINE" if snapshot.link else "OFFLINE",
            "ok" if snapshot.link else "bad",
        )
        for key_name, label in (
            ("engine", "Engine ECU"),
            ("transmission", "Transmission ECU"),
            ("body", "Body ECU"),
            ("gateway", "Gateway"),
        ):
            self.health_list.set_value(
                key_name,
                "OK" if snapshot.link else "NO DATA",
                "ok" if snapshot.link else "off",
            )

        for key_name in ("fl", "fr", "rl", "rr"):
            pressure = snapshot.tyre_pressure.get(key_name, 0.0)
            temp = snapshot.tyre_temp.get(key_name, 0.0)
            if pressure <= 0:
                self.tyre_list.set_value(key_name, "—", "off")
            else:
                state = (
                    "warn"
                    if pressure < TYRE_LOW_BAR or pressure > TYRE_HIGH_BAR
                    else "ok"
                )
                self.tyre_list.set_value(
                    key_name, f"{pressure:.2f} bar · {temp:.0f} °C", state
                )

        now = time.monotonic()
        if now - self._last_sample >= 0.8:
            self._last_sample = now
            self.temp_chart.push(snapshot.engine_temp_c)

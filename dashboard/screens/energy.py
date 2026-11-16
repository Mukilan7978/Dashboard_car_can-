from __future__ import annotations

import time

from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout

from config.settings import TANK_CAPACITY_L
from dashboard.theme import Theme
from dashboard.widgets.arc_gauge import PercentGauge
from dashboard.widgets.bars import BarGauge
from dashboard.widgets.card import Card, MetricCard
from dashboard.widgets.common import clamp
from dashboard.widgets.history_chart import HistoryChart
from .base import BaseScreen


class EnergyScreen(BaseScreen):
    def __init__(self, theme: Theme) -> None:
        super().__init__(theme)
        root = QHBoxLayout(self)
        root.setContentsMargins(18, 14, 18, 14)
        root.setSpacing(12)

        left = Card(theme, "Fuel and efficiency", "fuel")
        self.fuel_gauge = PercentGauge(theme)
        left.body.addWidget(self.fuel_gauge, 1)
        self.fuel_caption = QLabel("Fuel level decoded from CAN ID 0x104")
        self.fuel_caption.setObjectName("Subtle")
        self.fuel_caption.setWordWrap(True)
        left.body.addWidget(self.fuel_caption)
        root.addWidget(left, 4)

        right = QVBoxLayout()
        right.setSpacing(10)

        metrics = QHBoxLayout()
        metrics.setSpacing(8)
        self.range_card = MetricCard(theme, "Estimated range", "km", "trip")
        self.avg_card = MetricCard(theme, "Average consumption", "L/100km", "speed")
        self.instant_card = MetricCard(theme, "Instant consumption", "L/100km", "speed")
        self.avg_speed_card = MetricCard(theme, "Average speed", "km/h", "speed")
        for card in (
            self.range_card,
            self.avg_card,
            self.instant_card,
            self.avg_speed_card,
        ):
            metrics.addWidget(card, 1)
        right.addLayout(metrics, 0)

        charts = QHBoxLayout()
        charts.setSpacing(10)
        consumption_card = Card(theme, "Consumption history", "speed")
        self.consumption_chart = HistoryChart(
            theme, "Instant consumption", "L/100km", 0, 30
        )
        consumption_card.body.addWidget(self.consumption_chart, 1)
        charts.addWidget(consumption_card, 1)

        battery_card = Card(theme, "Battery history", "battery")
        self.battery_chart = HistoryChart(
            theme, "Battery voltage", "V", 8, 16, theme.blue
        )
        battery_card.body.addWidget(self.battery_chart, 1)
        charts.addWidget(battery_card, 1)
        right.addLayout(charts, 1)

        bars = QHBoxLayout()
        bars.setSpacing(8)
        self.load_card = Card(theme, "Engine load", "engine")
        self.load_gauge = BarGauge(theme, "", "%", 0, 100, warn_high=90, decimals=0)
        self.load_card.body.addWidget(self.load_gauge)
        bars.addWidget(self.load_card, 1)

        self.temp_card = Card(theme, "Engine temperature", "temperature")
        self.temp_gauge = BarGauge(
            theme, "", "°C", 0, 130, warn_high=110, decimals=0
        )
        self.temp_card.body.addWidget(self.temp_gauge)
        bars.addWidget(self.temp_card, 1)

        self.battery_card = Card(theme, "Battery voltage", "battery")
        self.battery_gauge = BarGauge(
            theme, "", "V", 8, 16, warn_low=11.8, decimals=1
        )
        self.battery_card.body.addWidget(self.battery_gauge)
        bars.addWidget(self.battery_card, 1)
        right.addLayout(bars, 0)

        root.addLayout(right, 7)
        self._last_sample = 0.0

    def refresh(self) -> None:
        snapshot = self.snapshot
        if snapshot is None:
            return
        self.fuel_gauge.set_value(snapshot.fuel_percent, snapshot.link)
        self.load_gauge.set_value(snapshot.engine_load)
        self.temp_gauge.set_value(snapshot.engine_temp_c)
        self.battery_gauge.set_value(snapshot.battery_v)

        fuel_fraction = clamp(snapshot.fuel_percent, 0.0, 100.0) / 100.0
        estimated_range = fuel_fraction * TANK_CAPACITY_L / 7.5 * 100.0
        self.range_card.set_value(f"{estimated_range:.0f}", detail="60 L tank")
        self.avg_card.set_value(
            f"{snapshot.avg_consumption:.1f}", detail=snapshot.driving_mode
        )
        self.instant_card.set_value(
            f"{snapshot.instant_consumption:.1f}",
            detail="Live CAN value",
        )
        self.avg_speed_card.set_value(
            f"{snapshot.avg_speed_kmh:.0f}", detail="Trip average"
        )

        now = time.monotonic()
        if now - self._last_sample >= 0.5:
            self._last_sample = now
            self.consumption_chart.push(snapshot.instant_consumption)
            self.battery_chart.push(snapshot.battery_v)

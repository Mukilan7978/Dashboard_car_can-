from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from dashboard.theme import Theme
from dashboard.widgets.card import Card, IconWidget
from dashboard.widgets.center_display import CenterDisplay
from .base import BaseScreen


class NavigationScreen(BaseScreen):
    def __init__(self, theme: Theme) -> None:
        super().__init__(theme)
        root = QHBoxLayout(self)
        root.setContentsMargins(18, 14, 18, 14)
        root.setSpacing(12)

        self.center_display = CenterDisplay(theme)
        root.addWidget(self.center_display, 7)

        route_card = Card(theme, "Simulated route", "trip")
        route_card.setMinimumWidth(330)
        route_card.setMaximumWidth(430)

        title = QLabel("Simulation HQ")
        title.setObjectName("SectionTitle")
        route_card.body.addWidget(title)
        subtitle = QLabel("Demo destination · 2.4 km · 6 min")
        subtitle.setObjectName("Subtle")
        route_card.body.addWidget(subtitle)

        stats = QHBoxLayout()
        stats.setSpacing(8)
        for value, label in (("2.4", "KM"), ("6", "MIN"), ("14:32", "ETA")):
            box = Card(theme)
            box.setObjectName("CardAlt")
            value_label = QLabel(value)
            value_label.setObjectName("CardValue")
            caption = QLabel(label)
            caption.setObjectName("CardUnit")
            box.body.addWidget(value_label)
            box.body.addWidget(caption)
            stats.addWidget(box, 1)
        route_card.body.addLayout(stats)

        steps = (
            ("left", "Head north on Simulation Ave", "250 m"),
            ("right", "Turn right onto Cockpit Road", "600 m"),
            ("right", "Continue onto CAN Boulevard", "1.1 km"),
            ("left", "Turn left at the roundabout", "450 m"),
            ("check", "Arrive at Simulation HQ", "Destination"),
        )
        for icon, text, distance in steps:
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 5, 0, 5)
            row_layout.setSpacing(10)
            row_layout.addWidget(IconWidget(icon, theme, 22), 0)
            labels = QVBoxLayout()
            labels.setSpacing(0)
            title_label = QLabel(text)
            title_label.setObjectName("Subtle")
            title_label.setWordWrap(True)
            distance_label = QLabel(distance)
            distance_label.setObjectName("Accent")
            labels.addWidget(title_label)
            labels.addWidget(distance_label)
            row_layout.addLayout(labels, 1)
            route_card.body.addWidget(row)

        route_card.body.addStretch(1)
        disclaimer = QLabel(
            "SIMULATED NAVIGATION ONLY\nNo GPS receiver, no map service, and no "
            "route guidance is performed."
        )
        disclaimer.setObjectName("Subtle")
        disclaimer.setWordWrap(True)
        disclaimer.setStyleSheet(
            f"color: {theme.amber}; font-size: 11px; line-height: 1.3;"
        )
        route_card.body.addWidget(disclaimer)
        root.addWidget(route_card, 3)

    def refresh(self) -> None:
        if self.snapshot is not None:
            self.center_display.set_snapshot(self.snapshot)

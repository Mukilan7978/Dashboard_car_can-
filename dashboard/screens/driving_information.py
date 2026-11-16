from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget, QGridLayout

from dashboard.theme import Theme
from .base import BaseScreen


class DrivingInformationScreen(BaseScreen):
    def __init__(self, theme: Theme) -> None:
        super().__init__(theme)
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 14, 18, 14)
        root.setSpacing(12)

        title = QLabel("Driving Information")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(title)

        grid = QGridLayout()
        grid.setSpacing(8)

        self.labels = {}
        fields = [
            ("Speed", "0 km/h"),
            ("Average Speed", "0 km/h"),
            ("Max Speed", "0 km/h"),
            ("Odometer", "0 km"),
            ("Trip Distance", "0 km"),
            ("Gear", "P"),
            ("Driving Mode", "COMFORT"),
        ]
        for i, (name, default) in enumerate(fields):
            lbl_name = QLabel(name)
            lbl_name.setAlignment(Qt.AlignmentFlag.AlignLeft)
            lbl_val = QLabel(default)
            lbl_val.setAlignment(Qt.AlignmentFlag.AlignRight)
            grid.addWidget(lbl_name, i, 0)
            grid.addWidget(lbl_val, i, 1)
            self.labels[name] = lbl_val

        root.addLayout(grid)

    def update_values(self, snapshot):
        # simple placeholder updates
        self.labels["Speed"].setText(f"{snapshot.speed_kmh:.1f} km/h")
        self.labels["Average Speed"].setText(f"{snapshot.avg_speed_kmh:.1f} km/h")
        self.labels["Max Speed"].setText(f"{max(snapshot.speed_kmh, 0):.1f} km/h")
        self.labels["Odometer"].setText(f"{snapshot.odometer_km:.1f} km")
        self.labels["Trip Distance"].setText(f"{snapshot.trip_km:.1f} km")
        self.labels["Gear"].setText(snapshot.gear_text or "P")
        mode = snapshot.driving_mode or "COMFORT"
        self.labels["Driving Mode"].setText(mode)

    def refresh(self) -> None:
        pass
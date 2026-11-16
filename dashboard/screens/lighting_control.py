from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget, QPushButton, QHBoxLayout

from dashboard.theme import Theme
from .base import BaseScreen


class LightingControlScreen(BaseScreen):
    def __init__(self, theme: Theme) -> None:
        super().__init__(theme)
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 14, 18, 14)
        root.setSpacing(12)

        # Header
        title = QLabel("Lighting Control")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(title)

        # Controls grid
        grid = QHBoxLayout()
        grid.setSpacing(12)

        btn_low = QPushButton("Low Beam")
        btn_low.clicked.connect(self._toggle_low)
        btn_high = QPushButton("High Beam")
        btn_high.clicked.connect(self._toggle_high)
        btn_fog = QPushButton("Fog Lamps")
        btn_fog.clicked.connect(self._toggle_fog)
        btn_park = QPushButton("Parking Lights")
        btn_park.clicked.connect(self._toggle_park)
        btn_left = QPushButton("Left Indicator")
        btn_left.clicked.connect(self._toggle_left)
        btn_right = QPushButton("Right Indicator")
        btn_right.clicked.connect(self._toggle_right)
        btn_hazard = QPushButton("Hazard Lights")
        btn_hazard.clicked.connect(self._toggle_hazard)

        grid.addWidget(btn_low)
        grid.addWidget(btn_high)
        grid.addWidget(btn_fog)
        grid.addWidget(btn_park)
        grid.addWidget(btn_left)
        grid.addWidget(btn_right)
        grid.addWidget(btn_hazard)

        root.addLayout(grid)

        self.status = QLabel("Status: —")
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self.status)

    def _toggle_low(self):
        self._send_light("low_beam")

    def _toggle_high(self):
        self._send_light("high_beam")

    def _toggle_fog(self):
        self._send_light("fog")

    def _toggle_park(self):
        self._send_light("parking")

    def _toggle_left(self):
        self._send_indicator("left")

    def _toggle_right(self):
        self._send_indicator("right")

    def _toggle_hazard(self):
        self._send_indicator("hazard")

    def _send_light(self, key):
        # forward to dashboard model via command
        from dashboard.main_window import MainWindow
        # we don't have reference; just emit a command through the snapshot path later
        pass

    def _send_indicator(self, side):
        pass

    def refresh(self) -> None:
        pass
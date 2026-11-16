from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from dashboard.theme import Theme
from .base import BaseScreen


class BatteryInformationScreen(BaseScreen):
    def __init__(self, theme: Theme) -> None:
        super().__init__(theme)
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 14, 18, 14)
        root.setSpacing(12)

        title = QLabel("Battery Information")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(title)

        self.labels = {}
        fields = [
            ("Battery Voltage", "12.6 V"),
            ("Charging Status", "—"),
            ("Battery Health", "—"),
            ("Electrical Warning", "—"),
        ]
        for i, (name, default) in enumerate(fields):
            lbl_name = QLabel(name)
            lbl_name.setAlignment(Qt.AlignmentFlag.AlignLeft)
            lbl_val = QLabel(default)
            lbl_val.setAlignment(Qt.AlignmentFlag.AlignRight)
            root.addWidget(lbl_name)
            root.addWidget(lbl_val)
            self.labels[name] = lbl_val

    def update_values(self, snapshot):
        self.labels["Battery Voltage"].setText(f"{snapshot.battery_v:.2f} V")
        # placeholder for charging status etc.

    def refresh(self) -> None:
        pass
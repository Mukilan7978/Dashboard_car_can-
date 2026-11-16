from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from dashboard.theme import Theme
from .base import BaseScreen


class VehicleSettingsScreen(BaseScreen):
    def __init__(self, theme: Theme) -> None:
        super().__init__(theme)
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 14, 18, 14)
        root.setSpacing(12)
        label = QLabel("Vehicle Settings Screen – placeholder")
        label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        root.addWidget(label)

    def refresh(self) -> None:
        pass
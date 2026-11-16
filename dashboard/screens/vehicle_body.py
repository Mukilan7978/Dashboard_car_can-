from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from dashboard.theme import Theme
from .base import BaseScreen


class VehicleBodyScreen(BaseScreen):
    def __init__(self, theme: Theme) -> None:
        super().__init__(theme)
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 14, 18, 14)
        root.setSpacing(12)
        label = QLabel("Vehicle Body Control Screen")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(label)

        # TODO: integrate 3D vehicle door/bonnet/boot controls

    def refresh(self) -> None:
        pass
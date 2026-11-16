from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from dashboard.theme import Theme
from .base import BaseScreen


class EngineInformationScreen(BaseScreen):
    def __init__(self, theme: Theme) -> None:
        super().__init__(theme)
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 14, 18, 14)
        root.setSpacing(12)

        title = QLabel("Engine Information")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(title)

        self.labels = {}
        fields = [
            ("RPM", "0"),
            ("Engine Temperature", "— °C"),
            ("Engine Load", "0 %"),
            ("Throttle Position", "0 %"),
            ("Engine Warning", "—"),
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
        self.labels["RPM"].setText(f"{snapshot.rpm:.0f}")
        self.labels["Engine Temperature"].setText(f"{snapshot.engine_temp_c:.0f} °C")
        self.labels["Engine Load"].setText(f"{snapshot.engine_load*100:.0f} %")
        self.labels["Throttle Position"].setText(f"{snapshot.clutch*100:.0f} %")  # placeholder
        # warning status could be added

    def refresh(self) -> None:
        pass
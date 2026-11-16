from __future__ import annotations

from typing import Any

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget

from dashboard.model import VehicleSnapshot
from dashboard.theme import Theme


class BaseScreen(QWidget):
    command_requested = Signal(dict)

    def __init__(self, theme: Theme, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.theme = theme
        self.snapshot: VehicleSnapshot | None = None

    def set_snapshot(self, snapshot: VehicleSnapshot) -> None:
        self.snapshot = snapshot
        self.refresh()

    def set_theme(self, theme: Theme) -> None:
        self.theme = theme
        for child in self.findChildren(QWidget):
            setter = getattr(child, "set_theme", None)
            if callable(setter):
                setter(theme)
        self.update()

    def send(self, name: str, **fields: Any) -> None:
        command = {"cmd": name}
        command.update(fields)
        self.command_requested.emit(command)

    def refresh(self) -> None:
        pass

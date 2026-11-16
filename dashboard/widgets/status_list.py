from __future__ import annotations

from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QPainter, QPen
from PySide6.QtWidgets import QWidget

from dashboard.theme import Theme
from .common import color, draw_text, font


class StatusList(QWidget):
    def __init__(self, theme: Theme, rows: int = 4,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.theme = theme
        self.items: list[tuple[str, str]] = []
        self.values: dict[str, tuple[str, str]] = {}
        self.rows = rows
        self.setMinimumHeight(rows * 27 + 8)

    def set_items(self, items: list[tuple[str, str]]) -> None:
        self.items = items
        self.rows = max(1, len(items))
        self.setMinimumHeight(self.rows * 27 + 8)
        self.update()

    def set_value(self, key: str, text: str, state: str = "ok") -> None:
        self.values[key] = (text, state)
        self.update()

    def clear_values(self) -> None:
        self.values.clear()
        self.update()

    def set_theme(self, theme: Theme) -> None:
        self.theme = theme
        self.update()

    def sizeHint(self) -> QSize:
        return QSize(240, self.rows * 27 + 8)

    def paintEvent(self, event: object) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        row_height = 27.0
        for index, (key, label) in enumerate(self.items):
            top = index * row_height + 4
            if index > 0:
                painter.setPen(QPen(color(self.theme.border, 120), 1))
                painter.drawLine(
                    QRectF(0, top - 2, self.width(), 1).topLeft(),
                    QRectF(0, top - 2, self.width(), 1).topRight(),
                )
            draw_text(
                painter,
                QRectF(0, top, self.width() * 0.58, row_height),
                label,
                font(8.6, 600),
                color(self.theme.muted),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            )
            value, state = self.values.get(key, ("—", "off"))
            if state == "ok":
                tint = self.theme.green
            elif state == "warn":
                tint = self.theme.amber
            elif state == "bad":
                tint = self.theme.red
            elif state == "info":
                tint = self.theme.accent
            else:
                tint = self.theme.faint
            dot_x = self.width() * 0.63
            painter.setBrush(color(tint))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(
                QRectF(dot_x, top + row_height / 2.0 - 3, 6, 6)
            )
            draw_text(
                painter,
                QRectF(dot_x + 14, top, self.width() - dot_x - 14, row_height),
                value,
                font(8.2, 700),
                color(tint),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
            )
        painter.end()

from __future__ import annotations

from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget

from dashboard.theme import Theme
from .common import color
from .numerals import draw_badge_text


class GearDisplay(QWidget):
    GEARS = ("P", "R", "N", "D", "M")

    def __init__(self, theme: Theme, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.theme = theme
        self.gear = "P"
        self.manual_gear = 1
        self.setMinimumHeight(58)
        self.setMaximumHeight(68)

    def sizeHint(self) -> QSize:
        return QSize(340, 62)

    def set_state(self, gear: str, manual_gear: int = 1) -> None:
        gear = gear if gear in self.GEARS else "P"
        manual = max(1, min(8, int(manual_gear)))
        if gear != self.gear or manual != self.manual_gear:
            self.gear = gear
            self.manual_gear = manual
            self.update()

    def set_theme(self, theme: Theme) -> None:
        self.theme = theme
        self.update()

    def paintEvent(self, event: object) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        rect = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        painter.setBrush(color(self.theme.surface))
        painter.setPen(QPen(color(self.theme.border), 1))
        painter.drawRoundedRect(rect, 14, 14)

        gap = 5.0
        inner = rect.adjusted(6, 6, -6, -6)
        cell_width = (inner.width() - gap * (len(self.GEARS) - 1)) / len(self.GEARS)
        for index, label in enumerate(self.GEARS):
            cell = QRectF(
                inner.left() + index * (cell_width + gap),
                inner.top(),
                cell_width,
                inner.height(),
            )
            active = label == self.gear
            if active:
                painter.setBrush(color(self.theme.accent))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRoundedRect(cell, 9, 9)
                text_color = color(self.theme.bg)
            else:
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.setPen(QPen(color(self.theme.border, 110), 1))
                painter.drawRoundedRect(cell, 9, 9)
                text_color = color(self.theme.faint)

            if active and label == "M":
                draw_badge_text(
                    painter,
                    QRectF(cell.left(), cell.top() + 2,
                           cell.width(), cell.height() * 0.62),
                    "M",
                    cell.height() * 0.42,
                    text_color,
                )
                badge = QRectF(
                    cell.center().x() - 9,
                    cell.bottom() - 20,
                    18,
                    16,
                )
                painter.setBrush(color(self.theme.bg))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRoundedRect(badge, 4, 4)
                draw_badge_text(
                    painter,
                    badge,
                    str(self.manual_gear),
                    cell.height() * 0.25,
                    color(self.theme.accent),
                )
            else:
                draw_badge_text(
                    painter,
                    cell,
                    label,
                    cell.height() * 0.44,
                    text_color,
                )
        painter.end()

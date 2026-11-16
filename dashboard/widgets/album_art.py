from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QColor,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QRadialGradient,
)
from PySide6.QtWidgets import QWidget

from dashboard.theme import Theme
from .common import color, draw_text, font


class AlbumArt(QWidget):
    def __init__(self, theme: Theme, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.theme = theme
        self.setMinimumSize(260, 260)

    def set_theme(self, theme: Theme) -> None:
        self.theme = theme
        self.update()

    def paintEvent(self, event: object) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        side = min(self.width(), self.height())
        rect = QRectF(
            (self.width() - side) / 2.0,
            (self.height() - side) / 2.0,
            side,
            side,
        ).adjusted(8, 8, -8, -8)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        clip = QPainterPath()
        clip.addRoundedRect(rect, side * 0.08, side * 0.08)
        painter.setClipPath(clip)
        gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        gradient.setColorAt(0.0, color(self.theme.accent_soft))
        gradient.setColorAt(0.55, color(self.theme.surface))
        gradient.setColorAt(1.0, color(self.theme.bg))
        painter.setBrush(gradient)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(rect)

        for index in range(4):
            radius = side * (0.18 + index * 0.10)
            center = QPointF(
                rect.center().x() + math.sin(index * 1.7) * side * 0.18,
                rect.center().y() + math.cos(index * 1.1) * side * 0.16,
            )
            radial = QRadialGradient(center, radius)
            tint = self.theme.accent2 if index % 2 == 0 else self.theme.accent
            radial.setColorAt(0.0, color(tint, 55))
            radial.setColorAt(1.0, color(tint, 0))
            painter.setBrush(radial)
            painter.drawEllipse(center, radius, radius)

        painter.setPen(QPen(color(self.theme.accent, 120), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        for index in range(7):
            inset = side * (0.10 + index * 0.022)
            painter.drawRoundedRect(rect.adjusted(inset, inset, -inset, -inset),
                                    side * 0.04, side * 0.04)

        line = QPainterPath()
        line.moveTo(rect.left() + side * 0.10, rect.bottom() - side * 0.32)
        for index in range(1, 7):
            x = rect.left() + side * (0.10 + index * 0.13)
            y = rect.bottom() - side * (0.32 + 0.08 * math.sin(index * 1.2))
            line.lineTo(x, y)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(color(self.theme.accent), max(2.0, side * 0.012),
                            Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawPath(line)

        draw_text(
            painter,
            QRectF(rect.left() + side * 0.08, rect.top() + side * 0.08,
                   rect.width() - side * 0.16, side * 0.10),
            "AUTOSIM SESSIONS",
            font(side * 0.038, 800, spacing=2.2),
            color(self.theme.text, 220),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
        )
        draw_text(
            painter,
            QRectF(rect.left() + side * 0.08, rect.bottom() - side * 0.18,
                   rect.width() - side * 0.16, side * 0.10),
            "SYNTHETIC ROADS",
            font(side * 0.030, 600, spacing=1.2),
            color(self.theme.muted),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
        )
        painter.end()

from __future__ import annotations

from collections import deque

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QLinearGradient, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QWidget

from dashboard.theme import Theme
from .common import clamp, color, draw_text, font


class HistoryChart(QWidget):
    def __init__(self, theme: Theme, title: str, unit: str,
                 minimum: float, maximum: float,
                 line_color: str | None = None,
                 length: int = 180,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.theme = theme
        self.title = title
        self.unit = unit
        self.minimum = minimum
        self.maximum = maximum
        self.line_color = line_color
        self.values: deque[float] = deque(maxlen=length)
        self.setMinimumHeight(130)

    def set_theme(self, theme: Theme) -> None:
        self.theme = theme
        self.update()

    def set_range(self, minimum: float, maximum: float) -> None:
        self.minimum = minimum
        self.maximum = maximum
        self.update()

    def push(self, value: float) -> None:
        self.values.append(clamp(float(value), self.minimum, self.maximum))
        self.update()

    def clear(self) -> None:
        self.values.clear()
        self.update()

    def paintEvent(self, event: object) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        rect = QRectF(self.rect())
        draw_text(
            painter,
            QRectF(rect.left(), rect.top(), rect.width() * 0.62, 18),
            self.title.upper(),
            font(8.0, 700, spacing=1.4),
            color(self.theme.muted),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
        )
        latest = self.values[-1] if self.values else 0.0
        draw_text(
            painter,
            QRectF(rect.left() + rect.width() * 0.50, rect.top(),
                   rect.width() * 0.50, 18),
            f"{latest:.1f} {self.unit}".strip(),
            font(9.6, 700),
            color(self.theme.text),
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
        )
        chart = QRectF(
            rect.left(),
            rect.top() + 28,
            rect.width(),
            max(20.0, rect.height() - 54),
        )
        painter.setBrush(color(self.theme.surface_alt, 130))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(chart, 6, 6)
        painter.setPen(QPen(color(self.theme.border, 100), 1))
        for fraction in (0.25, 0.50, 0.75):
            y = chart.top() + chart.height() * fraction
            painter.drawLine(QPointF(chart.left(), y), QPointF(chart.right(), y))
        for fraction in (0.25, 0.50, 0.75):
            x = chart.left() + chart.width() * fraction
            painter.drawLine(QPointF(x, chart.top()), QPointF(x, chart.bottom()))

        points = list(self.values)
        if len(points) >= 2:
            span = max(1, len(points) - 1)
            path = QPainterPath()
            for index, value in enumerate(points):
                fraction = (value - self.minimum) / max(
                    0.001, self.maximum - self.minimum
                )
                point = QPointF(
                    chart.left() + chart.width() * (index / span),
                    chart.bottom() - chart.height() * fraction,
                )
                if index == 0:
                    path.moveTo(point)
                else:
                    path.lineTo(point)
            fill = QPainterPath(path)
            fill.lineTo(chart.right(), chart.bottom())
            fill.lineTo(chart.left(), chart.bottom())
            fill.closeSubpath()
            tint = self.line_color or self.theme.accent
            gradient = QLinearGradient(chart.topLeft(), chart.bottomLeft())
            gradient.setColorAt(0.0, color(tint, 90))
            gradient.setColorAt(1.0, color(tint, 5))
            painter.setBrush(gradient)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawPath(fill)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(
                QPen(color(tint), 2.2, Qt.PenStyle.SolidLine,
                     Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
            )
            painter.drawPath(path)
            last = path.pointAtPercent(1.0)
            painter.setBrush(color(tint))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(last, 3.5, 3.5)
        else:
            draw_text(
                painter,
                chart,
                "COLLECTING DATA",
                font(8.0, 600, spacing=1.2),
                color(self.theme.muted, 170),
            )

        draw_text(
            painter,
            QRectF(chart.left(), chart.bottom() + 4, chart.width(), 18),
            f"{self.minimum:g}",
            font(6.8, 600),
            color(self.theme.faint),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
        )
        draw_text(
            painter,
            QRectF(chart.left(), chart.bottom() + 4, chart.width(), 18),
            f"{self.maximum:g}",
            font(6.8, 600),
            color(self.theme.faint),
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
        )
        painter.end()

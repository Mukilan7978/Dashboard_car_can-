from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QLinearGradient, QPainter, QPen
from PySide6.QtWidgets import QWidget

from dashboard.theme import Theme
from .common import clamp, color, draw_text, font
from .numerals import draw_badge_text


class BarGauge(QWidget):
    def __init__(self, theme: Theme, title: str, unit: str = "",
                 minimum: float = 0.0, maximum: float = 100.0,
                 warn_low: float | None = None,
                 warn_high: float | None = None,
                 decimals: int = 0, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.theme = theme
        self.title = title
        self.unit = unit
        self.minimum = minimum
        self.maximum = maximum
        self.warn_low = warn_low
        self.warn_high = warn_high
        self.decimals = decimals
        self.value = 0.0
        self.setMinimumHeight(52)
        self.setMinimumWidth(150)

    def set_value(self, value: float) -> None:
        value = clamp(float(value), self.minimum, self.maximum)
        if abs(value - self.value) > 0.001:
            self.value = value
            self.update()

    def set_theme(self, theme: Theme) -> None:
        self.theme = theme
        self.update()

    def _value_color(self) -> str:
        if self.warn_low is not None and self.value <= self.warn_low:
            return self.theme.amber
        if self.warn_high is not None and self.value >= self.warn_high:
            return self.theme.red
        return self.theme.accent

    def paintEvent(self, event: object) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        rect = QRectF(self.rect())
        draw_text(
            painter,
            QRectF(rect.left(), rect.top(), rect.width() * 0.62, 20),
            self.title.upper(),
            font(8.0, 700, spacing=1.5),
            color(self.theme.muted),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
        )
        value_text = f"{self.value:.{self.decimals}f}"
        value_rect = QRectF(
            rect.left() + rect.width() * 0.55, rect.top(),
            rect.width() * 0.45, 20,
        )
        value_size = 13.0
        unit_font = font(7.6, 700)
        painter.setFont(unit_font)
        unit_width = (
            painter.fontMetrics().horizontalAdvance(self.unit)
            if self.unit else 0.0
        )
        text_rect = QRectF(
            value_rect.left(), value_rect.top(),
            max(1.0, value_rect.width() - unit_width - 3.0),
            value_rect.height(),
        )
        draw_badge_text(
            painter,
            text_rect,
            value_text,
            value_size,
            color(self.theme.text),
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
        )
        if self.unit:
            draw_text(
                painter,
                QRectF(value_rect.right() - unit_width, value_rect.top(),
                       unit_width, value_rect.height()),
                self.unit,
                unit_font,
                color(self.theme.text),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
            )
        track = QRectF(rect.left(), rect.top() + 28, rect.width(), 7)
        painter.setBrush(color(self.theme.surface_alt))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(track, 3.5, 3.5)
        fraction = (self.value - self.minimum) / max(
            0.001, self.maximum - self.minimum
        )
        fill = QRectF(
            track.left(), track.top(), max(2.0, track.width() * fraction),
            track.height(),
        )
        gradient = QLinearGradient(fill.topLeft(), fill.topRight())
        gradient.setColorAt(0.0, color(self._value_color(), 170))
        gradient.setColorAt(1.0, color(self._value_color()))
        painter.setBrush(gradient)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(fill, 3.5, 3.5)
        painter.setBrush(color(self._value_color()))
        painter.drawEllipse(
            QRectF(fill.right() - 4, fill.center().y() - 4, 8, 8)
        )
        painter.end()


class SteeringBar(QWidget):
    def __init__(self, theme: Theme, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.theme = theme
        self.angle = 0.0
        self.setMinimumHeight(64)

    def set_angle(self, angle: float) -> None:
        angle = clamp(float(angle), -540.0, 540.0)
        if abs(angle - self.angle) > 0.2:
            self.angle = angle
            self.update()

    def set_theme(self, theme: Theme) -> None:
        self.theme = theme
        self.update()

    def paintEvent(self, event: object) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = QRectF(self.rect())
        draw_text(
            painter,
            QRectF(rect.left(), rect.top(), rect.width(), 18),
            "STEERING",
            font(8.0, 700, spacing=1.5),
            color(self.theme.muted),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
        )
        draw_badge_text(
            painter,
            QRectF(rect.left(), rect.top(), rect.width(), 18),
            f"{self.angle:+.0f}°",
            13.0,
            color(self.theme.text),
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
        )
        track = QRectF(rect.left(), rect.top() + 28, rect.width(), 6)
        painter.setBrush(color(self.theme.surface_alt))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(track, 3, 3)
        center = track.center().x()
        painter.setPen(QPen(color(self.theme.border), 1))
        painter.drawLine(center, track.top() - 2, center, track.bottom() + 2)
        pos = center + (self.angle / 540.0) * (track.width() / 2.0 - 4)
        painter.setBrush(color(self.theme.accent))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(pos - 5, track.center().y() - 5, 10, 10))
        painter.end()

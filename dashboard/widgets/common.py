from __future__ import annotations

import math
import time

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QWidget


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def lerp(start: float, end: float, amount: float) -> float:
    return start + (end - start) * amount


def approach(current: float, target: float, factor: float, dt: float) -> float:
    return current + (target - current) * min(1.0, factor * dt)


def font(size: float, weight: int = 500, family: str = "Lato",
         spacing: float = 0.0) -> QFont:
    value = QFont(family)
    value.setPointSizeF(max(6.0, size))
    value.setWeight(QFont.Weight(weight))
    if spacing:
        value.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, spacing)
    return value


def mono_font(size: float, weight: int = 400) -> QFont:
    return font(size, weight, "DejaVu Sans Mono")


def color(value: str, alpha: int | None = None) -> QColor:
    result = QColor(value)
    if alpha is not None:
        result.setAlpha(alpha)
    return result


def angle_point(center: QPointF, radius: float, degrees: float) -> QPointF:
    radians = math.radians(degrees)
    return QPointF(
        center.x() + math.cos(radians) * radius,
        center.y() - math.sin(radians) * radius,
    )


def draw_text(painter: QPainter, rect: QRectF, text: str, text_font: QFont,
              color_value: QColor, alignment: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignCenter) -> None:
    painter.setFont(text_font)
    painter.setPen(QPen(color_value))
    painter.drawText(rect, alignment, text)


def rounded_rect_path(rect: QRectF, radius: float) -> object:
    from PySide6.QtGui import QPainterPath

    path = QPainterPath()
    path.addRoundedRect(rect, radius, radius)
    return path


def with_alpha(color_value: QColor, alpha: int) -> QColor:
    result = QColor(color_value)
    result.setAlpha(alpha)
    return result


class AnimatedValue:
    def __init__(self, value: float = 0.0, speed: float = 25.0) -> None:
        self.value = float(value)
        self.target = float(value)
        self.speed = float(speed)
        self._last = time.monotonic()

    def set_target(self, target: float) -> None:
        self.target = float(target)

    def snap(self, value: float) -> None:
        self.value = float(value)
        self.target = float(value)
        self._last = time.monotonic()

    def update(self) -> float:
        now = time.monotonic()
        dt = min(0.05, max(0.0, now - self._last))
        self._last = now
        # Only move toward target if target differs from value by more than minimum step
        diff = self.target - self.value
        if abs(diff) < 0.01:
            self.value = self.target
        else:
            step = diff * min(1.0, dt * self.speed)
            self.value += step
        return self.value


class RepaintWidget(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

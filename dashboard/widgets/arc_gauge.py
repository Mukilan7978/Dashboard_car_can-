from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QColor,
    QConicalGradient,
    QPainter,
    QPen,
    QPixmap,
    QPolygonF,
    QRadialGradient,
)
from PySide6.QtWidgets import QSizePolicy, QWidget

from dashboard.theme import Theme
from .common import angle_point, clamp, color, draw_text, font
from .numerals import draw_badge_text


class ArcGauge(QWidget):
    minimum = 0.0
    maximum = 260.0
    major_step = 20.0
    minor_step = 10.0
    label_divisor = 1.0
    unit = "km/h"
    title = "SPEED"
    redline_start: float | None = None
    start_angle = 225.0
    sweep_angle = -270.0

    def __init__(self, theme: Theme, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.theme = theme
        self._value = 0.0
        self._link = True
        self._background: QPixmap | None = None
        self._background_key: tuple[int, int, float, str] | None = None
        self.setMinimumSize(310, 310)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

    def set_value(self, value: float, link: bool = True) -> None:
        new_value = clamp(float(value), self.minimum, self.maximum)
        # Only update if value changed significantly or link state changed
        if abs(new_value - self._value) > 0.5 or link != self._link:
            self._value = new_value
            self._link = link
            self.update()

    def set_theme(self, theme: Theme) -> None:
        self.theme = theme
        self._background = None
        self.update()

    def _geometry(self) -> tuple[QPointF, float]:
        size = min(self.width(), self.height())
        radius = max(10.0, size / 2.0 - 10.0)
        return QPointF(self.width() / 2.0, self.height() / 2.0), radius

    def _ensure_background(self) -> None:
        dpr = self.devicePixelRatioF()
        key = (self.width(), self.height(), dpr, self.theme.name)
        if self._background is not None and self._background_key == key:
            return
        pixmap = QPixmap(int(self.width() * dpr), int(self.height() * dpr))
        pixmap.setDevicePixelRatio(dpr)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        painter.scale(dpr, dpr)
        self._paint_background(painter)
        painter.end()
        self._background = pixmap
        self._background_key = key

    def _paint_background(self, painter: QPainter) -> None:
        center, radius = self._geometry()
        outer = QRectF(
            center.x() - radius,
            center.y() - radius,
            radius * 2.0,
            radius * 2.0,
        )

        shadow = QRadialGradient(center, radius * 1.02)
        shadow.setColorAt(0.0, color("#020407"))
        shadow.setColorAt(0.78, color("#020407", 235))
        shadow.setColorAt(1.0, color("#020407", 0))
        painter.setBrush(shadow)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(center, radius * 1.02, radius * 1.02)

        glass = QRadialGradient(center, radius * 0.94)
        glass.setColorAt(0.0, color("#0B1520"))
        glass.setColorAt(0.48, color(self.theme.surface, 245))
        glass.setColorAt(0.80, color(self.theme.bg, 250))
        glass.setColorAt(1.0, color("#010306"))
        painter.setBrush(glass)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(outer)

        bezel = QConicalGradient(center, 145.0)
        bezel.setColorAt(0.0, color("#BAC7D8"))
        bezel.setColorAt(0.18, color("#415066"))
        bezel.setColorAt(0.38, color("#101822"))
        bezel.setColorAt(0.64, color("#6E8098"))
        bezel.setColorAt(0.82, color("#202A38"))
        bezel.setColorAt(1.0, color("#C8D4E4"))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(bezel, max(1.5, radius * 0.020)))
        painter.drawEllipse(center, radius * 0.965, radius * 0.965)

        painter.setPen(
            QPen(color(self.theme.accent, 72), max(1.0, radius * 0.003))
        )
        painter.drawEllipse(center, radius * 0.90, radius * 0.90)

        track_rect = QRectF(
            center.x() - radius * 0.825,
            center.y() - radius * 0.825,
            radius * 1.65,
            radius * 1.65,
        )
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(
            QPen(color(self.theme.surface_alt, 225), radius * 0.036,
                 Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        )
        painter.drawArc(
            track_rect,
            int(self.start_angle * 16),
            int(self.sweep_angle * 16),
        )
        if self.redline_start is not None:
            fraction = (self.redline_start - self.minimum) / (
                self.maximum - self.minimum
            )
            painter.setPen(
                QPen(color(self.theme.red, 170), radius * 0.036,
                     Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            )
            painter.drawArc(
                track_rect,
                int((self.start_angle + self.sweep_angle * fraction) * 16),
                int(self.sweep_angle * (1.0 - fraction) * 16),
            )

        value = self.minimum
        while value <= self.maximum + 0.001:
            fraction = (value - self.minimum) / (self.maximum - self.minimum)
            angle = self.start_angle + self.sweep_angle * fraction
            major = abs(value / self.major_step - round(value / self.major_step)) < 1e-6
            inner = radius * (0.756 if major else 0.786)
            outer_tick = radius * 0.858
            in_redline = (
                self.redline_start is not None and value >= self.redline_start
            )
            if in_redline:
                tick_color = self.theme.red
            elif major:
                tick_color = self.theme.text
            else:
                tick_color = self.theme.muted
            painter.setPen(
                QPen(
                    color(tick_color, 235 if major else 135),
                    radius * (0.0062 if major else 0.0027),
                    Qt.PenStyle.SolidLine,
                    Qt.PenCapStyle.RoundCap,
                )
            )
            painter.drawLine(
                angle_point(center, inner, angle),
                angle_point(center, outer_tick, angle),
            )

            if major:
                label_point = angle_point(center, radius * 0.682, angle)
                label = str(int(round(value / self.label_divisor)))
                rect = QRectF(
                    label_point.x() - radius * 0.095,
                    label_point.y() - radius * 0.070,
                    radius * 0.19,
                    radius * 0.14,
                )
                draw_badge_text(
                    painter,
                    rect,
                    label,
                    max(7.8, radius * 0.070),
                    color(
                        self.theme.red if in_redline else self.theme.text,
                        235,
                    ),
                )
            value += self.minor_step

        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(
            QPen(color(self.theme.border, 190), max(1.0, radius * 0.002))
        )
        painter.drawEllipse(
            QRectF(
                center.x() - radius * 0.59,
                center.y() - radius * 0.59,
                radius * 1.18,
                radius * 1.18,
            )
        )

    def _value_fraction(self) -> float:
        return (self._value - self.minimum) / (self.maximum - self.minimum)

    def _painter_color(self) -> QColor:
        if not self._link:
            return color(self.theme.faint)
        if self.redline_start is not None and self._value >= self.redline_start:
            return color(self.theme.red)
        return color(self.theme.accent)

    def _track_rect(self, center: QPointF, radius: float) -> QRectF:
        return QRectF(
            center.x() - radius * 0.825,
            center.y() - radius * 0.825,
            radius * 1.65,
            radius * 1.65,
        )

    def _paint_progress(self, painter: QPainter) -> None:
        if self._value <= self.minimum:
            return
        center, radius = self._geometry()
        arc_rect = self._track_rect(center, radius)
        fraction = self._value_fraction()
        accent = color(self.theme.accent)
        red = color(self.theme.red)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(
            QPen(color(self.theme.accent, 40), radius * 0.074,
                 Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        )
        painter.drawArc(
            arc_rect,
            int(self.start_angle * 16),
            int(self.sweep_angle * fraction * 16),
        )
        if self.redline_start is not None and self._value > self.redline_start:
            red_fraction = (self.redline_start - self.minimum) / (
                self.maximum - self.minimum
            )
            painter.setPen(
                QPen(accent, radius * 0.036,
                     Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            )
            painter.drawArc(
                arc_rect,
                int(self.start_angle * 16),
                int(self.sweep_angle * red_fraction * 16),
            )
            painter.setPen(
                QPen(red, radius * 0.036,
                     Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            )
            painter.drawArc(
                arc_rect,
                int((self.start_angle + self.sweep_angle * red_fraction) * 16),
                int(self.sweep_angle * (fraction - red_fraction) * 16),
            )
        else:
            painter.setPen(
                QPen(accent, radius * 0.036,
                     Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            )
            painter.drawArc(
                arc_rect,
                int(self.start_angle * 16),
                int(self.sweep_angle * fraction * 16),
            )

    def _paint_needle(self, painter: QPainter) -> None:
        center, radius = self._geometry()
        fraction = self._value_fraction()
        angle = self.start_angle + self.sweep_angle * fraction
        needle_color = self._painter_color()
        tip = angle_point(center, radius * 0.735, angle)
        tail = angle_point(center, radius * 0.085, angle + 180.0)
        left = angle_point(center, radius * 0.018, angle + 90.0)
        right = angle_point(center, radius * 0.018, angle - 90.0)
        base_left = angle_point(center, radius * 0.038, angle + 90.0)
        base_right = angle_point(center, radius * 0.038, angle - 90.0)

        painter.setPen(
            QPen(QColor(
                needle_color.red(), needle_color.green(), needle_color.blue(), 62
            ), radius * 0.040, Qt.PenStyle.SolidLine,
                 Qt.PenCapStyle.RoundCap)
        )
        painter.drawLine(tail, tip)
        polygon = QPolygonF([base_left, left, tip, right, base_right])
        painter.setBrush(needle_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPolygon(polygon)
        painter.setPen(
            QPen(color("#FFFFFF", 120), max(1.0, radius * 0.002))
        )
        painter.drawLine(center, tip)

        painter.setBrush(color(self.theme.surface))
        painter.setPen(QPen(color(self.theme.border), max(1.0, radius * 0.006)))
        painter.drawEllipse(center, radius * 0.072, radius * 0.072)
        painter.setBrush(needle_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(center, radius * 0.042, radius * 0.042)
        painter.setBrush(color(self.theme.bg))
        painter.drawEllipse(center, radius * 0.016, radius * 0.016)

    def _digital_text(self) -> str:
        return f"{self._value:.0f}"

    def _digital_font_size(self, radius: float) -> float:
        return radius * 0.250

    def _paint_digital(self, painter: QPainter) -> None:
        center, radius = self._geometry()
        label_rect = QRectF(
            center.x() - radius * 0.42,
            center.y() - radius * 0.53,
            radius * 0.84,
            radius * 0.09,
        )
        draw_text(
            painter,
            label_rect,
            self.title,
            font(max(6.4, radius * 0.034), 750, spacing=3.4),
            color(self.theme.muted, 215),
        )
        value_rect = QRectF(
            center.x() - radius * 0.58,
            center.y() + radius * 0.12,
            radius * 1.16,
            radius * 0.30,
        )
        value_color = color(self.theme.text if self._link else self.theme.faint)
        draw_badge_text(
            painter,
            value_rect,
            self._digital_text(),
            self._digital_font_size(radius),
            value_color,
        )
        unit_rect = QRectF(
            center.x() - radius * 0.44,
            center.y() + radius * 0.405,
            radius * 0.88,
            radius * 0.09,
        )
        draw_text(
            painter,
            unit_rect,
            self.unit,
            font(max(7.0, radius * 0.043), 650, spacing=2.2),
            color(self.theme.muted, 225),
        )
        if self.redline_start is not None:
            marker = QRectF(
                center.x() - radius * 0.16,
                center.y() + radius * 0.53,
                radius * 0.32,
                radius * 0.022,
            )
            painter.setBrush(color(self.theme.red, 185))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(marker, marker.height() / 2, marker.height() / 2)

    def _paint_link_state(self, painter: QPainter) -> None:
        if self._link:
            return
        center, radius = self._geometry()
        rect = QRectF(
            center.x() - radius * 0.46,
            center.y() + radius * 0.57,
            radius * 0.92,
            radius * 0.085,
        )
        painter.setBrush(color(self.theme.amber, 26))
        painter.setPen(QPen(color(self.theme.amber, 120), 1))
        painter.drawRoundedRect(rect, radius * 0.042, radius * 0.042)
        draw_text(
            painter,
            rect,
            "NO CAN DATA",
            font(max(6.0, radius * 0.030), 700, spacing=1.5),
            color(self.theme.amber),
        )

    def paintEvent(self, event: object) -> None:
        self._ensure_background()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        if self._background is not None:
            painter.drawPixmap(0, 0, self._background)
        self._paint_progress(painter)
        self._paint_needle(painter)
        self._paint_digital(painter)
        self._paint_link_state(painter)
        painter.end()


class Speedometer(ArcGauge):
    maximum = 260.0
    major_step = 20.0
    minor_step = 10.0
    label_divisor = 1.0
    unit = "km/h"
    title = "SPEED"

    def _digital_text(self) -> str:
        return f"{self._value:.0f}"


class Tachometer(ArcGauge):
    maximum = 8000.0
    major_step = 1000.0
    minor_step = 250.0
    label_divisor = 1000.0
    unit = "x1000 RPM"
    title = "ENGINE SPEED"
    redline_start = 6500.0

    def _digital_text(self) -> str:
        return f"{self._value / 1000.0:.1f}"

    def _digital_font_size(self, radius: float) -> float:
        return radius * 0.225


class PercentGauge(ArcGauge):
    maximum = 100.0
    major_step = 10.0
    minor_step = 5.0
    label_divisor = 1.0
    unit = "%"
    title = "FUEL LEVEL"
    warn_low: float | None = 10.0

    def _digital_text(self) -> str:
        return f"{self._value:.0f}"

    def _digital_font_size(self, radius: float) -> float:
        return radius * 0.225

    def _painter_color(self) -> QColor:
        if not self._link:
            return color(self.theme.faint)
        if self.warn_low is not None and self._value <= self.warn_low:
            return color(self.theme.amber)
        return color(self.theme.accent)

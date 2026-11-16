from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import QLinearGradient, QPainter, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget

from config.settings import TANK_CAPACITY_L
from dashboard.model import VehicleSnapshot
from dashboard.theme import Theme
from .common import clamp, color, draw_text, font
from .icons import draw_icon
from .numerals import draw_badge_text, is_badge_text


class MetricStrip(QWidget):
    def __init__(self, theme: Theme, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.theme = theme
        self.snapshot: VehicleSnapshot | None = None
        self._signature: object | None = None
        self.setMinimumHeight(60)
        self.setMaximumHeight(400)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def set_theme(self, theme: Theme) -> None:
        self.theme = theme
        self._signature = None
        self.update()

    def set_snapshot(self, snapshot: VehicleSnapshot) -> None:
        signature = (
            snapshot.link,
            round(snapshot.fuel_percent, 1),
            round(snapshot.engine_temp_c, 1),
            round(snapshot.battery_v, 2),
            round(snapshot.avg_consumption, 1),
        )
        self.snapshot = snapshot
        if signature == self._signature:
            return
        self._signature = signature
        self.update()

    def sizeHint(self) -> QSize:
        return QSize(1200, 100)

    def paintEvent(self, event: object) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        scale = clamp(self.height() / 100.0, 0.7, 3.0)
        rect = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        gradient = QLinearGradient(rect.topLeft(), rect.topRight())
        gradient.setColorAt(0.0, color(self.theme.surface, 185))
        gradient.setColorAt(0.5, color(self.theme.surface_alt, 150))
        gradient.setColorAt(1.0, color(self.theme.surface, 185))
        painter.setBrush(gradient)
        painter.setPen(QPen(color(self.theme.border, 190), max(1.0, scale)))
        painter.drawRoundedRect(rect, 16 * scale, 16 * scale)

        snapshot = self.snapshot
        link = bool(snapshot and snapshot.link)
        fuel = snapshot.fuel_percent if snapshot else 0.0
        temp = snapshot.engine_temp_c if snapshot else 0.0
        battery = snapshot.battery_v if snapshot else 0.0
        consumption = snapshot.avg_consumption if snapshot else 0.0
        fuel_fraction = clamp(fuel, 0.0, 100.0) / 100.0
        estimated_range = fuel_fraction * TANK_CAPACITY_L / 7.5 * 100.0
        fuel_tint = (
            self.theme.red if link and fuel <= 10.0
            else self.theme.accent if link else self.theme.faint
        )
        temp_tint = (
            self.theme.red if link and temp >= 110.0
            else self.theme.amber if link and temp >= 100.0
            else self.theme.green if link else self.theme.faint
        )
        battery_tint = (
            self.theme.red if link and battery < 11.8
            else self.theme.green if link else self.theme.faint
        )

        items = (
            ("fuel", "FUEL", f"{fuel:.0f}" if link else "—", "%",
             fuel_tint, fuel_fraction),
            ("temperature", "COOLANT", f"{temp:.0f}" if link else "—", "°C",
             temp_tint, clamp(temp, 0.0, 130.0) / 130.0),
            ("trip", "RANGE", f"{estimated_range:.0f}" if link else "—", "KM",
             self.theme.accent if link else self.theme.faint, None),
            ("battery", "BATTERY", f"{battery:.1f}" if link else "—", "V",
             battery_tint, None),
            ("mode", "AVG USE", f"{consumption:.1f}" if link else "—", "L/100KM",
             self.theme.text if link else self.theme.faint, None),
        )
        width = rect.width() / len(items)
        for index, (icon, label, value, unit, tint, fraction) in enumerate(items):
            left = rect.left() + index * width
            cell = QRectF(left, rect.top(), width, rect.height())
            if index:
                painter.setPen(QPen(color(self.theme.border, 130), max(1.0, scale)))
                painter.drawLine(
                    QPointF(cell.left(), cell.top() + 16 * scale),
                    QPointF(cell.left(), cell.bottom() - 16 * scale),
                )
            icon_rect = QRectF(
                cell.left() + 18 * scale, cell.top() + 17 * scale,
                17 * scale, 17 * scale,
            )
            draw_icon(painter, icon, icon_rect, color(tint, 230))
            draw_text(
                painter,
                QRectF(cell.left() + 43 * scale, cell.top() + 13 * scale,
                       cell.width() - 50 * scale, 23 * scale),
                label,
                font(7.4 * scale, 700, spacing=1.6 * scale),
                color(self.theme.muted, 225),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            )
            value_rect = QRectF(
                cell.left() + 17 * scale, cell.top() + 36 * scale,
                cell.width() - 30 * scale, 34 * scale,
            )
            value_font_size = 22.0 * scale
            if link and is_badge_text(value):
                value_width = draw_badge_text(
                    painter,
                    value_rect,
                    value,
                    value_font_size,
                    color(tint),
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                )
            else:
                draw_text(
                    painter,
                    value_rect,
                    value,
                    font(21.0 * scale, 800, spacing=0.5 * scale),
                    color(tint),
                    Qt.AlignmentFlag.AlignLeft
                    | Qt.AlignmentFlag.AlignVCenter,
                )
                value_width = painter.fontMetrics().horizontalAdvance(value)
            draw_text(
                painter,
                QRectF(
                    value_rect.left() + value_width + 7 * scale,
                    value_rect.top() + 8 * scale,
                    max(24.0 * scale, value_rect.width() - value_width
                        - 7 * scale),
                    26 * scale,
                ),
                unit,
                font(7.0 * scale, 700, spacing=1.0 * scale),
                color(self.theme.muted, 220),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            )
            if fraction is not None:
                track = QRectF(
                    cell.left() + 18 * scale, cell.bottom() - 21 * scale,
                    cell.width() - 36 * scale, 4 * scale,
                )
                painter.setBrush(color(self.theme.surface, 240))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRoundedRect(track, 2 * scale, 2 * scale)
                fill = QRectF(track)
                fill.setWidth(track.width() * fraction)
                painter.setBrush(color(tint, 205))
                painter.drawRoundedRect(fill, 2 * scale, 2 * scale)
        painter.end()

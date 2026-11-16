from __future__ import annotations

import math
import time
from datetime import datetime, timedelta

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QColor,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPolygonF,
    QRadialGradient,
)
from PySide6.QtWidgets import QWidget

from dashboard.model import VehicleSnapshot
from dashboard.theme import Theme
from .common import color, draw_text, font
from .icons import draw_icon


class CenterDisplay(QWidget):
    def __init__(self, theme: Theme, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.theme = theme
        self.snapshot: VehicleSnapshot | None = None
        self.setMinimumSize(360, 320)

    def set_snapshot(self, snapshot: VehicleSnapshot) -> None:
        self.snapshot = snapshot
        self.update()

    def set_theme(self, theme: Theme) -> None:
        self.theme = theme
        self.update()

    def paintEvent(self, event: object) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        rect = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        gradient.setColorAt(0.0, color(self.theme.surface))
        gradient.setColorAt(1.0, color(self.theme.surface_alt))
        painter.setBrush(gradient)
        painter.setPen(QPen(color(self.theme.border), 1))
        painter.drawRoundedRect(rect, 18, 18)

        snapshot = self.snapshot
        painter.setBrush(Qt.BrushStyle.NoBrush)
        draw_icon(
            painter,
            "trip",
            QRectF(rect.left() + 18, rect.top() + 18, 22, 22),
            color(self.theme.accent),
        )
        draw_text(
            painter,
            QRectF(rect.left() + 48, rect.top() + 12, 280, 20),
            "SIMULATED NAVIGATION",
            font(9.0, 800, spacing=1.6),
            color(self.theme.text),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
        )
        draw_text(
            painter,
            QRectF(rect.left() + 48, rect.top() + 30, 300, 16),
            "DEMO ROUTE  ·  NOT REAL GPS",
            font(7.0, 600, spacing=0.8),
            color(self.theme.muted),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
        )

        if snapshot is not None:
            mode_text = f"{snapshot.driving_mode}  ·  {snapshot.gear_text}"
            draw_text(
                painter,
                QRectF(rect.right() - 230, rect.top() + 14, 210, 26),
                mode_text,
                font(8.4, 700, spacing=1.0),
                color(self.theme.accent),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
            )

        map_rect = QRectF(
            rect.left() + 16,
            rect.top() + 54,
            rect.width() - 32,
            rect.height() - 148,
        )
        self._draw_map(painter, map_rect, snapshot)

        if snapshot is not None and snapshot.warnings:
            warning = "   ".join(snapshot.warnings[:2])
            width = min(map_rect.width() - 24, 280.0)
            badge = QRectF(
                map_rect.right() - width - 10,
                map_rect.top() + 10,
                width,
                26,
            )
            painter.setBrush(color(self.theme.amber, 32))
            painter.setPen(QPen(color(self.theme.amber, 150), 1))
            painter.drawRoundedRect(badge, 8, 8)
            draw_text(
                painter,
                badge.adjusted(8, 0, -8, 0),
                warning,
                font(7.2, 700),
                color(self.theme.amber),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
            )

        bottom = QRectF(
            rect.left() + 16,
            rect.bottom() - 80,
            rect.width() - 32,
            64,
        )
        painter.setBrush(color(self.theme.bg, 155))
        painter.setPen(QPen(color(self.theme.border), 1))
        painter.drawRoundedRect(bottom, 12, 12)

        arrow_box = QRectF(bottom.left() + 12, bottom.top() + 10, 44, 44)
        painter.setBrush(color(self.theme.accent, 30))
        painter.setPen(QPen(color(self.theme.accent, 120), 1))
        painter.drawRoundedRect(arrow_box, 10, 10)
        self._draw_turn_arrow(painter, arrow_box.adjusted(9, 9, -9, -9))

        draw_text(
            painter,
            QRectF(bottom.left() + 68, bottom.top() + 8, bottom.width() - 180, 22),
            "Turn right onto Simulation Ave",
            font(10.0, 700),
            color(self.theme.text),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
        )
        draw_text(
            painter,
            QRectF(bottom.left() + 68, bottom.top() + 30, bottom.width() - 180, 20),
            "in 250 m   ·   2.4 km total",
            font(8.0, 600),
            color(self.theme.muted),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
        )
        eta = datetime.now() + timedelta(minutes=6)
        draw_text(
            painter,
            QRectF(bottom.right() - 110, bottom.top() + 10, 92, 20),
            "ETA  " + eta.strftime("%H:%M"),
            font(8.4, 700),
            color(self.theme.accent),
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
        )
        draw_text(
            painter,
            QRectF(bottom.right() - 110, bottom.top() + 32, 92, 18),
            "6 min",
            font(7.0, 600),
            color(self.theme.muted),
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
        )
        painter.end()

    def _draw_map(self, painter: QPainter, rect: QRectF,
                  snapshot: VehicleSnapshot | None) -> None:
        painter.save()
        clip = QPainterPath()
        clip.addRoundedRect(rect, 12, 12)
        painter.setClipPath(clip)
        painter.setBrush(color("#050B12"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(rect)

        step = max(28.0, rect.width() / 14.0)
        painter.setPen(QPen(color(self.theme.border, 80), 1))
        x = rect.left() - step
        while x < rect.right() + step:
            painter.drawLine(QPointF(x, rect.top()), QPointF(x, rect.bottom()))
            x += step
        y = rect.top() - step
        while y < rect.bottom() + step:
            painter.drawLine(QPointF(rect.left(), y), QPointF(rect.right(), y))
            y += step

        blocks = (
            (0.04, 0.08, 0.20, 0.20), (0.30, 0.04, 0.16, 0.28),
            (0.54, 0.10, 0.26, 0.18), (0.83, 0.06, 0.13, 0.32),
            (0.06, 0.36, 0.16, 0.26), (0.28, 0.40, 0.22, 0.16),
            (0.56, 0.36, 0.12, 0.30), (0.74, 0.42, 0.20, 0.20),
            (0.12, 0.70, 0.24, 0.18), (0.42, 0.64, 0.18, 0.24),
            (0.66, 0.68, 0.26, 0.18),
        )
        for bx, by, bw, bh in blocks:
            block = QRectF(
                rect.left() + rect.width() * bx,
                rect.top() + rect.height() * by,
                rect.width() * bw,
                rect.height() * bh,
            )
            painter.setBrush(color(self.theme.surface_alt, 180))
            painter.setPen(QPen(color(self.theme.border, 120), 1))
            painter.drawRoundedRect(block, 5, 5)

        route_points = (
            (0.10, 0.86), (0.10, 0.62), (0.36, 0.62), (0.36, 0.36),
            (0.62, 0.36), (0.62, 0.20), (0.88, 0.20),
        )
        route = QPainterPath()
        first = True
        for px, py in route_points:
            point = QPointF(
                rect.left() + rect.width() * px,
                rect.top() + rect.height() * py,
            )
            if first:
                route.moveTo(point)
                first = False
            else:
                route.lineTo(point)

        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(
            QPen(color(self.theme.accent, 45), 15,
                 Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap,
                 Qt.PenJoinStyle.RoundJoin)
        )
        painter.drawPath(route)
        painter.setPen(
            QPen(color(self.theme.accent), 5,
                 Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap,
                 Qt.PenJoinStyle.RoundJoin)
        )
        painter.drawPath(route)
        painter.setPen(
            QPen(color("#FFFFFF", 130), 1.5,
                 Qt.PenStyle.DashLine, Qt.PenCapStyle.RoundCap)
        )
        painter.drawPath(route)

        percent = 0.33 + 0.10 * math.sin(time.monotonic() * 0.8)
        car_point = route.pointAtPercent(percent)
        tangent_point = route.pointAtPercent(min(0.999, percent + 0.01))
        angle = math.degrees(
            math.atan2(tangent_point.y() - car_point.y(),
                       tangent_point.x() - car_point.x())
        )
        pulse = 15.0 + 5.0 * math.sin(time.monotonic() * 3.0)
        glow = QRadialGradient(car_point, pulse)
        glow.setColorAt(0.0, color(self.theme.accent, 130))
        glow.setColorAt(1.0, color(self.theme.accent, 0))
        painter.setBrush(glow)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(car_point, pulse, pulse)

        painter.save()
        painter.translate(car_point)
        painter.rotate(angle)
        car = QPolygonF([
            QPointF(9, 0), QPointF(-6, 6), QPointF(-3, 0), QPointF(-6, -6),
        ])
        painter.setBrush(color("#FFFFFF"))
        painter.setPen(QPen(color(self.theme.bg), 1))
        painter.drawPolygon(car)
        painter.restore()

        destination = route.pointAtPercent(1.0)
        painter.setBrush(color(self.theme.green))
        painter.setPen(QPen(color("#03110A"), 2))
        painter.drawEllipse(destination, 8, 8)
        painter.setBrush(color(self.theme.bg))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(destination, 3, 3)

        draw_text(
            painter,
            QRectF(rect.left() + 10, rect.bottom() - 24, 220, 18),
            "SIMULATED MAP  ·  NO GPS",
            font(6.6, 600, spacing=1.0),
            color(self.theme.muted, 150),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
        )

        if snapshot is not None and not snapshot.link:
            painter.setBrush(color(self.theme.bg, 205))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(rect)
            draw_text(
                painter,
                rect,
                "NO CAN DATA",
                font(12.0, 800, spacing=2.0),
                color(self.theme.amber),
            )
        painter.restore()

    def _draw_turn_arrow(self, painter: QPainter, rect: QRectF) -> None:
        path = QPainterPath()
        x0 = rect.left()
        y0 = rect.top()
        w = rect.width()
        h = rect.height()
        path.moveTo(x0 + w * 0.20, y0 + h * 0.82)
        path.lineTo(x0 + w * 0.20, y0 + h * 0.48)
        path.cubicTo(
            x0 + w * 0.20, y0 + h * 0.22,
            x0 + w * 0.36, y0 + h * 0.18,
            x0 + w * 0.62, y0 + h * 0.18,
        )
        path.lineTo(x0 + w * 0.62, y0 + h * 0.06)
        path.lineTo(x0 + w * 0.90, y0 + h * 0.28)
        path.lineTo(x0 + w * 0.62, y0 + h * 0.50)
        path.lineTo(x0 + w * 0.62, y0 + h * 0.36)
        path.cubicTo(
            x0 + w * 0.44, y0 + h * 0.36,
            x0 + w * 0.38, y0 + h * 0.40,
            x0 + w * 0.38, y0 + h * 0.56,
        )
        path.lineTo(x0 + w * 0.38, y0 + h * 0.82)
        path.closeSubpath()
        painter.setBrush(color(self.theme.accent))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPath(path)

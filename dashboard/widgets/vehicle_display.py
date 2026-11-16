from __future__ import annotations

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

from dashboard.model import VehicleSnapshot
from dashboard.theme import Theme
from .common import color, draw_text, font


class VehicleDisplay(QWidget):
    def __init__(self, theme: Theme, parent: QWidget | None = None,
                 compact: bool = False) -> None:
        super().__init__(parent)
        self.theme = theme
        self.snapshot: VehicleSnapshot | None = None
        self._signature: object | None = None
        self.compact = compact
        if compact:
            self.setMinimumSize(220, 200)
        else:
            self.setMinimumSize(260, 340)

    def set_snapshot(self, snapshot: VehicleSnapshot) -> None:
        signature = (
            snapshot.gear_text,
            snapshot.driving_mode,
            snapshot.left_indicator,
            snapshot.right_indicator,
            snapshot.hazard,
            snapshot.low_beam,
            snapshot.high_beam,
            snapshot.drl,
            snapshot.fog,
            snapshot.brake_light,
            snapshot.reverse_light,
            tuple(sorted(snapshot.doors.items())),
            snapshot.bonnet,
            snapshot.boot,
            snapshot.mirror_l,
            snapshot.mirror_r,
        )
        self.snapshot = snapshot
        if signature == self._signature:
            return
        self._signature = signature
        self.update()

    def set_theme(self, theme: Theme) -> None:
        self.theme = theme
        self._signature = None
        self.update()

    def _scale(self) -> tuple[QPointF, float]:
        side = min(self.width() * 0.78, self.height() * 0.88)
        return QPointF(self.width() / 2.0, self.height() / 2.0), side

    def _pt(self, center: QPointF, side: float, x: float, y: float) -> QPointF:
        return QPointF(center.x() + x * side, center.y() + y * side)

    def _rect(self, center: QPointF, side: float, x: float, y: float,
              w: float, h: float) -> QRectF:
        return QRectF(center.x() + (x - w / 2.0) * side,
                      center.y() + (y - h / 2.0) * side, w * side, h * side)

    def _body_path(self, center: QPointF, side: float) -> QPainterPath:
        path = QPainterPath()
        path.moveTo(self._pt(center, side, -0.15, -0.43))
        path.cubicTo(
            self._pt(center, side, -0.24, -0.38),
            self._pt(center, side, -0.27, -0.29),
            self._pt(center, side, -0.27, -0.18),
        )
        path.lineTo(self._pt(center, side, -0.27, 0.30))
        path.cubicTo(
            self._pt(center, side, -0.27, 0.39),
            self._pt(center, side, -0.22, 0.43),
            self._pt(center, side, -0.15, 0.44),
        )
        path.lineTo(self._pt(center, side, 0.15, 0.44))
        path.cubicTo(
            self._pt(center, side, 0.22, 0.43),
            self._pt(center, side, 0.27, 0.39),
            self._pt(center, side, 0.27, 0.30),
        )
        path.lineTo(self._pt(center, side, 0.27, -0.18))
        path.cubicTo(
            self._pt(center, side, 0.27, -0.29),
            self._pt(center, side, 0.24, -0.38),
            self._pt(center, side, 0.15, -0.43),
        )
        path.closeSubpath()
        return path

    def _glow(self, painter: QPainter, center: QPointF, radius: float,
              color_value: QColor, strength: int = 150) -> None:
        gradient = QRadialGradient(center, radius)
        gradient.setColorAt(0.0, QColor(color_value.red(), color_value.green(),
                                        color_value.blue(), strength))
        gradient.setColorAt(1.0, QColor(color_value.red(), color_value.green(),
                                        color_value.blue(), 0))
        painter.setBrush(gradient)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(center, radius, radius)

    def paintEvent(self, event: object) -> None:
        snapshot = self.snapshot
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        center, side = self._scale()

        painter.setBrush(QColor(0, 0, 0, 90))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(self._rect(center, side, 0, 0.02, 0.64, 0.94))

        if snapshot is None:
            draw_text(
                painter, QRectF(self.rect()), "AWAITING CAN",
                font(12, 600, spacing=2.0), color(self.theme.muted),
            )
            painter.end()
            return

        body = self._body_path(center, side)
        gradient = QLinearGradient(
            QPointF(center.x(), center.y() - side * 0.44),
            QPointF(center.x(), center.y() + side * 0.44),
        )
        gradient.setColorAt(0.0, color(self.theme.surface_alt))
        gradient.setColorAt(0.55, color(self.theme.surface))
        gradient.setColorAt(1.0, color(self.theme.bg))
        painter.setBrush(gradient)
        painter.setPen(QPen(color(self.theme.border), max(1.0, side * 0.005)))
        painter.drawPath(body)

        self._draw_wheels(painter, center, side)
        self._draw_surfaces(painter, center, side)
        self._draw_lights(painter, center, side, snapshot)
        self._draw_doors(painter, center, side, snapshot)
        self._draw_mirrors(painter, center, side, snapshot)
        self._draw_body_warnings(painter, center, side, snapshot)

        if not self.compact:
            label = f"{snapshot.gear_text}  {snapshot.driving_mode}"
            draw_text(
                painter,
                QRectF(center.x() - side * 0.4, center.y() + side * 0.47,
                       side * 0.8, side * 0.08),
                label,
                font(max(8.0, side * 0.032), 700, spacing=2.0),
                color(self.theme.muted),
            )
        painter.end()

    def _draw_wheels(self, painter: QPainter, center: QPointF, side: float) -> None:
        painter.setBrush(color("#040506"))
        painter.setPen(QPen(color(self.theme.border, 190), max(1.0, side * 0.004)))
        for x in (-0.285, 0.285):
            for y in (-0.27, 0.27):
                wheel = self._rect(center, side, x, y, 0.065, 0.15)
                painter.drawRoundedRect(wheel, side * 0.02, side * 0.02)
                rim = wheel.adjusted(
                    wheel.width() * 0.24, wheel.height() * 0.13,
                    -wheel.width() * 0.24, -wheel.height() * 0.13,
                )
                painter.setBrush(color(self.theme.surface_alt, 190))
                painter.setPen(QPen(color(self.theme.muted, 120),
                                    max(1.0, side * 0.002)))
                painter.drawRoundedRect(rim, side * 0.009, side * 0.009)
                painter.setBrush(color(self.theme.faint, 150))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(rim.center(), side * 0.005, side * 0.005)

    def _draw_surfaces(self, painter: QPainter, center: QPointF, side: float) -> None:
        windshield = QPainterPath()
        windshield.moveTo(self._pt(center, side, -0.19, -0.10))
        windshield.lineTo(self._pt(center, side, 0.19, -0.10))
        windshield.lineTo(self._pt(center, side, 0.15, -0.24))
        windshield.lineTo(self._pt(center, side, -0.15, -0.24))
        windshield.closeSubpath()
        painter.setBrush(color(self.theme.accent_soft, 170))
        painter.setPen(QPen(color(self.theme.accent, 110), max(1.0, side * 0.003)))
        painter.drawPath(windshield)

        rear = QPainterPath()
        rear.moveTo(self._pt(center, side, -0.17, 0.23))
        rear.lineTo(self._pt(center, side, 0.17, 0.23))
        rear.lineTo(self._pt(center, side, 0.13, 0.33))
        rear.lineTo(self._pt(center, side, -0.13, 0.33))
        rear.closeSubpath()
        painter.setBrush(color(self.theme.accent_soft, 130))
        painter.drawPath(rear)

        roof = QRectF(
            center.x() - side * 0.15,
            center.y() - side * 0.09,
            side * 0.30,
            side * 0.31,
        )
        painter.setBrush(color(self.theme.surface, 180))
        painter.setPen(QPen(color(self.theme.border, 160), max(1.0, side * 0.003)))
        painter.drawRoundedRect(roof, side * 0.04, side * 0.04)

        painter.setPen(QPen(color(self.theme.border, 190), max(1.0, side * 0.003)))
        painter.drawLine(
            self._pt(center, side, -0.24, -0.34),
            self._pt(center, side, 0.24, -0.34),
        )
        painter.drawLine(
            self._pt(center, side, -0.24, 0.36),
            self._pt(center, side, 0.24, 0.36),
        )
        painter.setPen(QPen(color(self.theme.faint, 120), max(1.0, side * 0.002)))
        painter.drawLine(
            self._pt(center, side, 0.00, -0.24),
            self._pt(center, side, 0.00, 0.33),
        )

        painter.setPen(QPen(color(self.theme.border, 115), max(1.0, side * 0.002)))
        for x in (-0.16, 0.16):
            painter.drawLine(
                self._pt(center, side, x, -0.34),
                self._pt(center, side, x * 0.72, -0.22),
            )
            painter.drawLine(
                self._pt(center, side, x, 0.22),
                self._pt(center, side, x * 0.82, 0.35),
            )
        for x in (-0.17, 0.17):
            painter.drawLine(
                self._pt(center, side, x, -0.30),
                self._pt(center, side, x, 0.30),
            )

        painter.setBrush(color(self.theme.surface_alt, 220))
        painter.setPen(QPen(color(self.theme.muted, 130), max(1.0, side * 0.002)))
        for x in (-0.026, 0.026):
            painter.drawRoundedRect(
                self._rect(center, side, x, -0.392, 0.042, 0.040),
                side * 0.008, side * 0.008,
            )
        painter.setPen(QPen(color(self.theme.faint, 150), max(1.0, side * 0.0015)))
        for x in (-0.026, 0.026):
            for offset in (-0.009, 0.0, 0.009):
                painter.drawLine(
                    self._pt(center, side, x + offset, -0.407),
                    self._pt(center, side, x + offset, -0.377),
                )

        painter.setBrush(color(self.theme.accent, 200))
        painter.setPen(QPen(color("#FFFFFF", 100), max(1.0, side * 0.0015)))
        painter.drawEllipse(self._pt(center, side, 0.0, -0.285),
                            side * 0.012, side * 0.012)

    def _draw_lights(self, painter: QPainter, center: QPointF, side: float,
                     snapshot: VehicleSnapshot) -> None:
        head_on = snapshot.low_beam or snapshot.high_beam or snapshot.drl
        head_color = color("#E8F4FF") if head_on else color(self.theme.faint, 120)
        if snapshot.high_beam:
            painter.setBrush(QColor(230, 244, 255, 24))
            painter.setPen(Qt.PenStyle.NoPen)
            for x in (-0.16, 0.16):
                beam = QPainterPath()
                beam.moveTo(self._pt(center, side, x - 0.045, -0.40))
                beam.lineTo(self._pt(center, side, x + 0.045, -0.40))
                beam.lineTo(self._pt(center, side, x + 0.20, -0.72))
                beam.lineTo(self._pt(center, side, x - 0.20, -0.72))
                beam.closeSubpath()
                painter.drawPath(beam)
        if head_on:
            for x in (-0.16, 0.16):
                self._glow(painter, self._pt(center, side, x, -0.405),
                           side * 0.10, head_color, 100)
        painter.setBrush(head_color)
        painter.setPen(QPen(color(self.theme.border, 180), max(1.0, side * 0.003)))
        for x in (-0.16, 0.16):
            painter.drawRoundedRect(
                self._rect(center, side, x, -0.405, 0.105, 0.035),
                side * 0.015, side * 0.015,
            )

        rear_on = snapshot.brake_light or snapshot.headlight_on
        rear_color = color(self.theme.red) if rear_on else color(self.theme.faint, 110)
        if rear_on:
            for x in (-0.175, 0.175):
                self._glow(painter, self._pt(center, side, x, 0.42),
                           side * 0.085, color(self.theme.red), 90)
        painter.setBrush(rear_color)
        for x in (-0.175, 0.175):
            painter.drawRoundedRect(
                self._rect(center, side, x, 0.42, 0.105, 0.030),
                side * 0.012, side * 0.012,
            )

        if snapshot.left_indicator or snapshot.right_indicator or snapshot.hazard:
            if snapshot.left_indicator or snapshot.hazard:
                for y in (-0.315, 0.315):
                    point = self._pt(center, side, -0.265, y)
                    self._glow(painter, point, side * 0.055,
                               color(self.theme.amber), 160)
                    painter.setBrush(color(self.theme.amber))
                    painter.drawEllipse(point, side * 0.016, side * 0.016)
            if snapshot.right_indicator or snapshot.hazard:
                for y in (-0.315, 0.315):
                    point = self._pt(center, side, 0.265, y)
                    self._glow(painter, point, side * 0.055,
                               color(self.theme.amber), 160)
                    painter.setBrush(color(self.theme.amber))
                    painter.drawEllipse(point, side * 0.016, side * 0.016)

        if snapshot.reverse_light:
            painter.setBrush(QColor(245, 250, 255))
            painter.setPen(Qt.PenStyle.NoPen)
            for x in (-0.06, 0.06):
                painter.drawEllipse(
                    self._pt(center, side, x, 0.425),
                    side * 0.012, side * 0.012,
                )

    def _draw_doors(self, painter: QPainter, center: QPointF, side: float,
                    snapshot: VehicleSnapshot) -> None:
        painter.setPen(QPen(color(self.theme.border, 210), max(1.0, side * 0.003)))
        painter.drawLine(
            self._pt(center, side, -0.265, -0.12),
            self._pt(center, side, 0.265, -0.12),
        )
        painter.drawLine(
            self._pt(center, side, -0.265, 0.08),
            self._pt(center, side, 0.265, 0.08),
        )
        painter.drawLine(
            self._pt(center, side, -0.265, 0.24),
            self._pt(center, side, 0.265, 0.24),
        )
        painter.setBrush(color(self.theme.muted, 170))
        painter.setPen(Qt.PenStyle.NoPen)
        for x in (-0.245, 0.245):
            painter.drawRoundedRect(
                self._rect(center, side, x, -0.02, 0.03, 0.012),
                side * 0.005, side * 0.005,
            )
            painter.drawRoundedRect(
                self._rect(center, side, x, 0.16, 0.03, 0.012),
                side * 0.005, side * 0.005,
            )

        door_defs = (
            ("fl", -1, -0.12),
            ("rl", -1, 0.08),
            ("fr", 1, -0.12),
            ("rr", 1, 0.08),
        )
        for key, direction, hinge_y in door_defs:
            if not snapshot.doors[key]:
                continue
            hinge = self._pt(center, side, 0.255 * direction, hinge_y)
            painter.save()
            painter.translate(hinge)
            painter.rotate(-32 * direction)
            panel = QRectF(
                0.0 if direction < 0 else -side * 0.035,
                0.0,
                side * 0.035,
                side * 0.20,
            )
            painter.setBrush(color(self.theme.surface_alt, 235))
            painter.setPen(QPen(color(self.theme.amber, 220), max(1.0, side * 0.005)))
            painter.drawRoundedRect(panel, side * 0.012, side * 0.012)
            painter.restore()
            point = self._pt(center, side, 0.34 * direction, hinge_y + 0.10)
            draw_text(
                painter,
                QRectF(point.x() - side * 0.04, point.y() - side * 0.025,
                       side * 0.08, side * 0.05),
                key.upper(),
                font(max(5.0, side * 0.022), 800),
                color(self.theme.amber),
            )

    def _draw_mirrors(self, painter: QPainter, center: QPointF, side: float,
                      snapshot: VehicleSnapshot) -> None:
        painter.setBrush(color(self.theme.surface_alt))
        painter.setPen(QPen(color(self.theme.border), max(1.0, side * 0.003)))
        for direction, folded in ((-1, snapshot.mirror_l), (1, snapshot.mirror_r)):
            x = 0.305 if not folded else 0.283
            painter.drawRoundedRect(
                self._rect(center, side, x * direction, -0.17, 0.055, 0.026),
                side * 0.008, side * 0.008,
            )

    def _draw_body_warnings(self, painter: QPainter, center: QPointF, side: float,
                            snapshot: VehicleSnapshot) -> None:
        if snapshot.bonnet:
            painter.setPen(QPen(color(self.theme.amber), max(1.5, side * 0.006),
                                Qt.PenStyle.DashLine))
            painter.drawLine(
                self._pt(center, side, -0.20, -0.37),
                self._pt(center, side, 0.20, -0.37),
            )
            draw_text(
                painter,
                QRectF(center.x() - side * 0.16, center.y() - side * 0.35,
                       side * 0.32, side * 0.05),
                "BONNET",
                font(max(5.0, side * 0.022), 800, spacing=1.0),
                color(self.theme.amber),
            )
        if snapshot.boot:
            painter.setPen(QPen(color(self.theme.amber), max(1.5, side * 0.006),
                                Qt.PenStyle.DashLine))
            painter.drawLine(
                self._pt(center, side, -0.20, 0.39),
                self._pt(center, side, 0.20, 0.39),
            )
            draw_text(
                painter,
                QRectF(center.x() - side * 0.16, center.y() + side * 0.30,
                       side * 0.32, side * 0.05),
                "BOOT",
                font(max(5.0, side * 0.022), 800, spacing=1.0),
                color(self.theme.amber),
            )

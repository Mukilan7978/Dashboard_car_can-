from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPen
from PySide6.QtWidgets import QWidget

from dashboard.model import VehicleSnapshot
from dashboard.theme import Theme
from .common import clamp, color, draw_text, font
from .icons import draw_icon


class HeaderBar(QWidget):
    def __init__(self, theme: Theme, channel: str = "vcan0",
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.theme = theme
        self.channel = channel
        self.snapshot: VehicleSnapshot | None = None
        self.setFixedHeight(66)

    def set_snapshot(self, snapshot: VehicleSnapshot) -> None:
        self.snapshot = snapshot
        self.update()

    def set_theme(self, theme: Theme) -> None:
        self.theme = theme
        self.update()

    def set_channel(self, channel: str) -> None:
        self.channel = channel
        self.update()

    def paintEvent(self, event: object) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        rect = QRectF(self.rect())
        painter.setBrush(color(self.theme.bg, 245))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(rect)
        painter.setPen(QPen(color(self.theme.border), 1))
        painter.drawLine(rect.bottomLeft(), rect.bottomRight())

        scale = clamp(self.height() / 66.0, 0.78, 2.6)
        pad = 20.0 * scale
        emblem = QRectF(pad, 14.0 * scale, 38.0 * scale, 38.0 * scale)
        gradient = QLinearGradient(emblem.topLeft(), emblem.bottomRight())
        gradient.setColorAt(0.0, color(self.theme.accent))
        gradient.setColorAt(1.0, color(self.theme.accent2))
        painter.setBrush(gradient)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(emblem, 12 * scale, 12 * scale)
        draw_text(
            painter, emblem, "A",
            font(20 * scale, 800), color(self.theme.bg),
        )

        brand_left = emblem.right() + 12 * scale
        draw_text(
            painter,
            QRectF(brand_left, 13 * scale, 150 * scale, 24 * scale),
            "AUTOSIM",
            font(15 * scale, 800, spacing=2.5 * scale),
            color(self.theme.text),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
        )
        draw_text(
            painter,
            QRectF(brand_left, 34 * scale, 150 * scale, 18 * scale),
            "COCKPIT  /  SIMULATED",
            font(7.2 * scale, 600, spacing=1.2 * scale),
            color(self.theme.muted),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
        )

        snapshot = self.snapshot
        mode = snapshot.driving_mode if snapshot else "COMFORT"
        chip = QRectF(
            brand_left + 152 * scale, 18 * scale, 108 * scale, 30 * scale
        )
        painter.setBrush(color(self.theme.accent, 34))
        painter.setPen(QPen(color(self.theme.accent, 150), 1))
        painter.drawRoundedRect(chip, 15 * scale, 15 * scale)
        draw_text(
            painter, chip, mode,
            font(8.2 * scale, 800, spacing=1.2 * scale),
            color(self.theme.accent),
        )

        indicators = self._indicator_definitions(snapshot)
        start_x = chip.right() + 24 * scale
        cell = 32.0 * scale
        gap = 5.0 * scale
        for index, (name, active, tint) in enumerate(indicators):
            box = QRectF(
                start_x + index * (cell + gap), 17 * scale, cell, 32 * scale
            )
            if box.right() > self.width() - 360 * scale:
                break
            if active:
                painter.setBrush(color(tint, 28))
                painter.setPen(QPen(color(tint, 115), 1))
                painter.drawRoundedRect(box, 8 * scale, 8 * scale)
                icon_color = color(tint)
            else:
                icon_color = color(self.theme.faint, 80)
            draw_icon(
                painter,
                name,
                box.adjusted(6 * scale, 6 * scale, -6 * scale, -6 * scale),
                icon_color,
            )

        right = self.width() - pad
        now = datetime.now()
        draw_text(
            painter,
            QRectF(right - 70 * scale, 11 * scale, 70 * scale, 24 * scale),
            now.strftime("%H:%M"),
            font(15 * scale, 700),
            color(self.theme.text),
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
        )
        draw_text(
            painter,
            QRectF(right - 120 * scale, 33 * scale, 120 * scale, 18 * scale),
            now.strftime("%a %d %b"),
            font(7.2 * scale, 600, spacing=0.8 * scale),
            color(self.theme.muted),
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
        )

        link = bool(snapshot and snapshot.link)
        status_color = self.theme.green if link else self.theme.red
        dot = QPointF(right - 178 * scale, 27 * scale)
        painter.setBrush(color(status_color, 50))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(dot, 9 * scale, 9 * scale)
        painter.setBrush(color(status_color))
        painter.drawEllipse(dot, 4 * scale, 4 * scale)
        draw_text(
            painter,
            QRectF(right - 292 * scale, 13 * scale, 104 * scale, 18 * scale),
            "CAN LINK" if link else "NO CAN LINK",
            font(7.6 * scale, 700, spacing=1.0 * scale),
            color(status_color),
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
        )
        draw_text(
            painter,
            QRectF(right - 292 * scale, 32 * scale, 104 * scale, 18 * scale),
            self.channel.upper(),
            font(7.0 * scale, 600),
            color(self.theme.muted),
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
        )
        ambient = snapshot.ambient_temp_c if snapshot else 0.0
        ambient_text = f"{ambient:.1f}°C" if snapshot and snapshot.link else "--.-°C"
        draw_text(
            painter,
            QRectF(right - 366 * scale, 13 * scale, 60 * scale, 38 * scale),
            ambient_text,
            font(10.5 * scale, 600),
            color(self.theme.text),
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
        )
        painter.end()

    def _indicator_definitions(
        self, snapshot: VehicleSnapshot | None
    ) -> list[tuple[str, bool, str]]:
        if snapshot is None:
            return [("left", False, self.theme.green)]
        return [
            ("left", snapshot.left_indicator or snapshot.hazard, self.theme.green),
            ("right", snapshot.right_indicator or snapshot.hazard, self.theme.green),
            ("low_beam", snapshot.low_beam, self.theme.green),
            ("high_beam", snapshot.high_beam, self.theme.blue),
            ("fog", snapshot.fog, self.theme.green),
            ("seatbelt", not snapshot.seatbelt, self.theme.red),
            ("park_brake", snapshot.parking_brake, self.theme.red),
            ("battery", snapshot.battery_low, self.theme.red),
            ("engine", snapshot.check_engine, self.theme.amber),
            ("fuel", snapshot.fuel_low, self.theme.amber),
            ("door", snapshot.any_door_open, self.theme.amber),
            ("tyre", snapshot.tyre_warning, self.theme.amber),
        ]


class FooterBar(QWidget):
    def __init__(self, theme: Theme, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.theme = theme
        self.snapshot: VehicleSnapshot | None = None
        self.setFixedHeight(40)

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
        rect = QRectF(self.rect())
        painter.setBrush(color(self.theme.bg, 245))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(rect)
        painter.setPen(QPen(color(self.theme.border), 1))
        painter.drawLine(rect.topLeft(), rect.topRight())

        snapshot = self.snapshot
        if snapshot is None:
            painter.end()
            return
        scale = clamp(self.height() / 40.0, 0.78, 2.6)
        left = 20.0 * scale
        draw_text(
            painter,
            QRectF(left, 0, 200 * scale, self.height()),
            f"ODO  {snapshot.odometer_km:,.1f} km",
            font(8.4 * scale, 700, spacing=0.8 * scale),
            color(self.theme.text),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
        )
        draw_text(
            painter,
            QRectF(left + 190 * scale, 0, 180 * scale, self.height()),
            f"TRIP  {snapshot.trip_km:,.1f} km",
            font(8.4 * scale, 600, spacing=0.8 * scale),
            color(self.theme.muted),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
        )

        if not snapshot.link:
            status = "NO CAN LINK"
            status_color = self.theme.red
        elif snapshot.gear == "P":
            status = "PARKED"
            status_color = self.theme.muted
        elif snapshot.speed_abs < 1.0:
            status = "READY"
            status_color = self.theme.green
        else:
            status = "DRIVING"
            status_color = self.theme.green
        draw_text(
            painter,
            QRectF(self.width() / 2.0 - 180 * scale, 0, 360 * scale,
                   self.height()),
            status,
            font(8.4 * scale, 800, spacing=2.0 * scale),
            color(status_color),
        )
        if snapshot.warnings:
            warning_text = snapshot.warnings[0]
            if len(snapshot.warnings) > 1:
                warning_text += f"  +{len(snapshot.warnings) - 1}"
            draw_text(
                painter,
                QRectF(self.width() / 2.0 - 180 * scale, 0, 360 * scale,
                       self.height()),
                warning_text,
                font(8.2 * scale, 700),
                color(self.theme.amber),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
            )

        draw_text(
            painter,
            QRectF(self.width() - 500 * scale, 0, 480 * scale, self.height()),
            "E  ENGINE    G  GEAR    ↑↓  DRIVE    F1-F7  SCREENS    F11  FULL",
            font(7.4 * scale, 600, spacing=0.8 * scale),
            color(self.theme.muted),
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
        )
        painter.end()

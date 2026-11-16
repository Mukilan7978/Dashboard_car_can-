from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, Signal
from PySide6.QtGui import (
    QConicalGradient,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QRadialGradient,
)
from PySide6.QtWidgets import (
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from dashboard.model import VehicleSnapshot
from dashboard.theme import Theme
from .common import color, draw_text, font
from .numerals import draw_badge_text
from .vehicle_display import VehicleDisplay


class Roundel(QWidget):
    def __init__(self, theme: Theme, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.theme = theme
        self.running = False
        self.setFixedSize(96, 96)

    def set_theme(self, theme: Theme) -> None:
        self.theme = theme
        self.update()

    def set_running(self, running: bool) -> None:
        if running != self.running:
            self.running = running
            self.update()

    def paintEvent(self, event: object) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        center = QPointF(self.width() / 2.0, self.height() / 2.0)
        radius = min(self.width(), self.height()) / 2.0 - 3.0

        if self.running:
            glow = QRadialGradient(center, radius * 1.22)
            glow.setColorAt(0.0, color(self.theme.accent, 0))
            glow.setColorAt(0.72, color(self.theme.accent, 0))
            glow.setColorAt(1.0, color(self.theme.accent, 65))
            painter.setBrush(glow)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(center, radius * 1.22, radius * 1.22)

        bezel = QConicalGradient(center, 140.0)
        bezel.setColorAt(0.0, color("#E2E8F0"))
        bezel.setColorAt(0.22, color("#8293A8"))
        bezel.setColorAt(0.50, color("#222D3C"))
        bezel.setColorAt(0.74, color("#B7C4D4"))
        bezel.setColorAt(1.0, color("#5E7088"))
        painter.setBrush(bezel)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(center, radius, radius)

        painter.setBrush(color("#05080D"))
        painter.drawEllipse(center, radius * 0.87, radius * 0.87)

        inner = radius * 0.79
        clip = QPainterPath()
        clip.addEllipse(center, inner, inner)
        painter.save()
        painter.setClipPath(clip)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color("#F7FBFF"))
        painter.drawEllipse(center, inner, inner)
        painter.setBrush(color(self.theme.accent))
        quadrants = (
            QRectF(center.x() - inner, center.y() - inner, inner, inner),
            QRectF(center.x(), center.y(), inner, inner),
        )
        for quadrant in quadrants:
            painter.drawRect(quadrant)
        painter.restore()

        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(color("#05080D", 175), max(1.0, radius * 0.025)))
        painter.drawEllipse(center, inner * 0.50, inner * 0.50)
        painter.setBrush(color("#060A10"))
        painter.setPen(QPen(color("#B8C9DE", 170), max(1.0, radius * 0.018)))
        painter.drawEllipse(center, inner * 0.45, inner * 0.45)
        draw_text(
            painter,
            QRectF(center.x() - inner * 0.4, center.y() - inner * 0.4,
                   inner * 0.8, inner * 0.8),
            "A",
            font(radius * 0.42, 800),
            color("#F4F8FF"),
        )
        draw_text(
            painter,
            QRectF(center.x() - radius * 0.68, center.y() + radius * 0.64,
                   radius * 1.36, radius * 0.15),
            "AUTOSIM",
            font(radius * 0.095, 800, spacing=2.0),
            color(self.theme.muted, 210),
        )
        painter.end()


class ClusterStatus(QWidget):
    def __init__(self, theme: Theme, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.theme = theme
        self.snapshot: VehicleSnapshot | None = None
        self._signature: object | None = None
        self.scale = 1.0
        self.setMinimumHeight(86)
        self.setMaximumHeight(96)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def set_scale(self, scale: float) -> None:
        scale = max(0.7, min(2.6, scale))
        if abs(scale - self.scale) < 0.01:
            return
        self.scale = scale
        self.setMinimumHeight(round(86 * scale))
        self.setMaximumHeight(round(96 * scale))
        self.update()

    def set_theme(self, theme: Theme) -> None:
        self.theme = theme
        self._signature = None
        self.update()

    def set_snapshot(self, snapshot: VehicleSnapshot) -> None:
        signature = (
            snapshot.link,
            snapshot.gear_text,
            snapshot.driving_mode,
            snapshot.engine_running,
            tuple(snapshot.warnings),
        )
        self.snapshot = snapshot
        if signature == self._signature:
            return
        self._signature = signature
        self.update()

    def paintEvent(self, event: object) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        scale = self.scale
        rect = QRectF(self.rect()).adjusted(2 * scale, 0, -2 * scale, 0)
        snapshot = self.snapshot
        width = rect.width() / 3.0
        columns = (
            (rect.left(), "GEAR"),
            (rect.left() + width, "MODE"),
            (rect.left() + width * 2.0, "IGNITION"),
        )
        for index, (left, label) in enumerate(columns):
            column = QRectF(left, rect.top(), width, rect.height())
            draw_text(
                painter,
                QRectF(column.left(), column.top() + 2 * scale,
                       column.width(), 15 * scale),
                label,
                font(7.0 * scale, 700, spacing=1.8 * scale),
                color(self.theme.muted, 220),
            )
            if index:
                painter.setPen(QPen(color(self.theme.border, 150), 1))
                painter.drawLine(
                    QPointF(column.left(), column.top() + 14 * scale),
                    QPointF(column.left(), column.bottom() - 22 * scale),
                )

        if snapshot is not None:
            gear = snapshot.gear_text
            mode = snapshot.driving_mode
            running = snapshot.engine_running
        else:
            gear, mode, running = "P", "COMFORT", False

        gear_rect = QRectF(
            rect.left(), rect.top() + 14 * scale, width,
            rect.height() - 38 * scale,
        )
        draw_badge_text(
            painter, gear_rect, gear, 42.0 * scale,
            color(self.theme.text)
            if snapshot and snapshot.link else color(self.theme.faint),
        )
        mode_rect = QRectF(
            rect.left() + width, rect.top() + 18 * scale, width,
            rect.height() - 42 * scale,
        )
        draw_text(
            painter, mode_rect, mode if mode else "COMFORT",
            font(16.5 * scale, 700, spacing=1.2 * scale),
            color(self.theme.accent)
            if snapshot and snapshot.link else color(self.theme.faint),
        )
        status_rect = QRectF(
            rect.left() + width * 2.0, rect.top() + 17 * scale, width,
            rect.height() - 40 * scale,
        )
        if snapshot and not snapshot.link:
            status_text = "NO CAN"
            status_color = self.theme.amber
        elif running:
            status_text = "RUNNING"
            status_color = self.theme.green
        else:
            status_text = "ENGINE OFF"
            status_color = self.theme.muted
        draw_text(
            painter, status_rect, status_text,
            font(13.0 * scale, 800, spacing=1.4 * scale),
            color(status_color),
        )

        warnings = snapshot.warnings if snapshot else []
        warning_rect = QRectF(
            rect.left(), rect.bottom() - 23 * scale, rect.width(), 20 * scale
        )
        if warnings:
            text = "   •   ".join(warnings[:2])
            tint = self.theme.amber
        elif snapshot and snapshot.link:
            text = "ALL SYSTEMS NOMINAL"
            tint = self.theme.green
        else:
            text = "AWAITING CAN DATA"
            tint = self.theme.muted
        draw_text(
            painter, warning_rect, text,
            font(7.2 * scale, 700, spacing=1.0 * scale),
            color(tint, 220),
        )
        painter.end()


class ClusterCenter(QWidget):
    engine_toggle = Signal()

    def __init__(self, theme: Theme, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.theme = theme
        self.snapshot: VehicleSnapshot | None = None
        self._button_state: tuple[bool, bool, str, float] | None = None
        self.scale = 1.0

        self._root = QVBoxLayout(self)
        self._root.setContentsMargins(18, 12, 18, 14)
        self._root.setSpacing(2)

        self.roundel = Roundel(theme)
        self._root.addWidget(self.roundel, 0, Qt.AlignmentFlag.AlignHCenter)
        self._root.addSpacing(2)

        self.vehicle = VehicleDisplay(theme, compact=True)
        self._root.addWidget(self.vehicle, 1)

        self.status = ClusterStatus(theme)
        self._root.addWidget(self.status, 0)

        self.start_button = QPushButton("START ENGINE")
        self.start_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.start_button.setFixedHeight(44)
        self.start_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.start_button.clicked.connect(self.engine_toggle.emit)
        self._root.addWidget(self.start_button, 0)

    def set_scale(self, scale: float) -> None:
        scale = max(0.7, min(2.6, scale))
        if abs(scale - self.scale) < 0.01:
            return
        self.scale = scale
        self._root.setContentsMargins(
            round(18 * scale), round(12 * scale),
            round(18 * scale), round(14 * scale),
        )
        self._root.setSpacing(max(1, round(2 * scale)))
        self.roundel.setFixedSize(round(96 * scale), round(96 * scale))
        self.status.set_scale(scale)
        self.start_button.setFixedHeight(round(44 * scale))
        self._button_state = None
        if self.snapshot is not None:
            self._sync_button(self.snapshot)
        self.update()

    def set_theme(self, theme: Theme) -> None:
        self.theme = theme
        self.roundel.set_theme(theme)
        self.vehicle.set_theme(theme)
        self.status.set_theme(theme)
        self._button_state = None
        if self.snapshot is not None:
            self._sync_button(self.snapshot)
        self.update()

    def set_snapshot(self, snapshot: VehicleSnapshot) -> None:
        self.snapshot = snapshot
        self.roundel.set_running(snapshot.engine_running)
        self.vehicle.set_snapshot(snapshot)
        self.status.set_snapshot(snapshot)
        self._sync_button(snapshot)

    def _sync_button(self, snapshot: VehicleSnapshot) -> None:
        running = snapshot.engine_running
        link = snapshot.link
        state = (running, link, self.theme.name, self.scale)
        if state == self._button_state:
            return
        self._button_state = state
        if running:
            text = "STOP ENGINE"
            tint = self.theme.red
            text_color = "#FFF4F4"
        else:
            text = "START ENGINE"
            tint = self.theme.accent
            text_color = self.theme.text
        if not link:
            text = "ENGINE CONTROL OFFLINE"
        self.start_button.setText(text)
        self.start_button.setStyleSheet(
            f"QPushButton {{"
            f" background-color: {self.theme.surface_alt};"
            f" color: {text_color};"
            f" border: 1px solid {tint};"
            f" border-radius: {round(10 * self.scale)}px;"
            f" font-family: 'Lato';"
            f" font-size: {round(11 * self.scale)}px;"
            f" font-weight: 800;"
            f" letter-spacing: {max(1, round(2 * self.scale))}px;"
            f"}}"
            f"QPushButton:hover {{ background-color: {tint};"
            f" color: {self.theme.bg}; }}"
            f"QPushButton:pressed {{ background-color: {self.theme.accent_soft}; }}"
        )

    def paintEvent(self, event: object) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        scale = self.scale
        rect = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        gradient.setColorAt(0.0, color(self.theme.surface, 210))
        gradient.setColorAt(0.55, color(self.theme.surface_alt, 150))
        gradient.setColorAt(1.0, color(self.theme.surface, 230))
        painter.setBrush(gradient)
        painter.setPen(QPen(color(self.theme.border, 210), max(1.0, scale)))
        painter.drawRoundedRect(rect, 20 * scale, 20 * scale)

        painter.setPen(
            QPen(color(self.theme.accent, 125), 1.4,
                 Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        )
        painter.drawLine(
            QPointF(rect.left() + rect.width() * 0.24, rect.top() + 1),
            QPointF(rect.right() - rect.width() * 0.24, rect.top() + 1),
        )
        painter.setPen(QPen(color(self.theme.border, 105), max(1.0, scale)))
        painter.drawLine(
            QPointF(rect.left() + 18 * scale, rect.top() + 84 * scale),
            QPointF(rect.right() - 18 * scale, rect.top() + 84 * scale),
        )
        painter.end()

    def sizeHint(self) -> QSize:
        return QSize(440, 580)

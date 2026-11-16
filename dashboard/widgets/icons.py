from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QPolygonF

_NAME_ALIASES = {
    "low": "low_beam",
    "high": "high_beam",
    "brake": "park_brake",
    "temp": "temperature",
    "park": "park_brake",
}


def _norm(rect: QRectF, x: float, y: float) -> QPointF:
    return QPointF(rect.left() + rect.width() * x, rect.top() + rect.height() * y)


def _poly(rect: QRectF, points: list[tuple[float, float]]) -> QPolygonF:
    return QPolygonF([_norm(rect, x, y) for x, y in points])


def _stroke(painter: QPainter, color: QColor, rect: QRectF) -> None:
    width = max(1.2, min(rect.width(), rect.height()) * 0.085)
    painter.setPen(
        QPen(color, width, Qt.PenStyle.SolidLine,
             Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    )
    painter.setBrush(Qt.BrushStyle.NoBrush)


def draw_icon(painter: QPainter, name: str, rect: QRectF, color: QColor) -> None:
    name = _NAME_ALIASES.get(name, name)
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    size = min(rect.width(), rect.height())
    _stroke(painter, color, rect)
    width = max(1.2, size * 0.085)

    if name in ("left", "right"):
        if name == "left":
            points = [
                (0.10, 0.50), (0.36, 0.24), (0.36, 0.38), (0.88, 0.38),
                (0.88, 0.62), (0.36, 0.62), (0.36, 0.76),
            ]
        else:
            points = [
                (0.90, 0.50), (0.64, 0.24), (0.64, 0.38), (0.12, 0.38),
                (0.12, 0.62), (0.64, 0.62), (0.64, 0.76),
            ]
        painter.setBrush(color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPolygon(_poly(rect, points))

    elif name == "low_beam":
        painter.setBrush(color)
        painter.drawEllipse(_norm(rect, 0.22, 0.42), size * 0.20, size * 0.20)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        for offset in (0.38, 0.50, 0.62):
            painter.drawLine(
                _norm(rect, 0.42, offset), _norm(rect, 0.83, offset - 0.07)
            )
        painter.drawLine(_norm(rect, 0.16, 0.23), _norm(rect, 0.16, 0.77))

    elif name == "high_beam":
        painter.setBrush(Qt.BrushStyle.NoBrush)
        for offset in (0.30, 0.42, 0.54):
            painter.drawLine(_norm(rect, 0.16, offset), _norm(rect, 0.86, offset))
        for offset in (0.25, 0.37, 0.49, 0.61):
            painter.drawLine(
                _norm(rect, 0.22, offset), _norm(rect, 0.40, offset - 0.10)
            )

    elif name == "drl":
        painter.setBrush(color)
        painter.drawEllipse(_norm(rect, 0.26, 0.50), size * 0.18, size * 0.18)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        for offset in (0.32, 0.44, 0.56):
            painter.drawLine(
                _norm(rect, 0.50, offset), _norm(rect, 0.80, offset)
            )

    elif name == "fog":
        painter.setBrush(color)
        painter.drawEllipse(_norm(rect, 0.25, 0.55), size * 0.16, size * 0.16)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        for offset in (0.30, 0.50, 0.70):
            painter.drawLine(
                _norm(rect, 0.50, offset), _norm(rect, 0.86, offset + 0.10)
            )
            painter.drawLine(
                _norm(rect, 0.56, offset + 0.13), _norm(rect, 0.72, offset + 0.24)
            )

    elif name == "battery":
        painter.drawRoundedRect(
            QRectF(rect.left() + size * 0.10, rect.top() + size * 0.28,
                   size * 0.66, size * 0.46),
            size * 0.06, size * 0.06,
        )
        painter.drawLine(_norm(rect, 0.22, 0.20), _norm(rect, 0.22, 0.28))
        painter.drawLine(_norm(rect, 0.44, 0.20), _norm(rect, 0.44, 0.28))
        painter.drawLine(_norm(rect, 0.76, 0.46), _norm(rect, 0.90, 0.46))
        painter.drawLine(_norm(rect, 0.83, 0.39), _norm(rect, 0.83, 0.53))
        painter.drawLine(_norm(rect, 0.30, 0.64), _norm(rect, 0.58, 0.64))

    elif name == "engine":
        path = QPainterPath()
        path.moveTo(_norm(rect, 0.16, 0.40))
        path.lineTo(_norm(rect, 0.34, 0.40))
        path.lineTo(_norm(rect, 0.42, 0.28))
        path.lineTo(_norm(rect, 0.70, 0.28))
        path.lineTo(_norm(rect, 0.82, 0.40))
        path.lineTo(_norm(rect, 0.84, 0.68))
        path.lineTo(_norm(rect, 0.70, 0.78))
        path.lineTo(_norm(rect, 0.30, 0.78))
        path.lineTo(_norm(rect, 0.22, 0.66))
        path.lineTo(_norm(rect, 0.16, 0.66))
        path.closeSubpath()
        painter.drawPath(path)
        painter.drawLine(_norm(rect, 0.34, 0.28), _norm(rect, 0.34, 0.16))
        painter.drawLine(_norm(rect, 0.52, 0.28), _norm(rect, 0.52, 0.16))
        painter.drawLine(_norm(rect, 0.70, 0.28), _norm(rect, 0.70, 0.16))

    elif name == "fuel":
        painter.drawRoundedRect(
            QRectF(rect.left() + size * 0.18, rect.top() + size * 0.20,
                   size * 0.40, size * 0.68),
            size * 0.05, size * 0.05,
        )
        painter.drawRect(
            QRectF(rect.left() + size * 0.25, rect.top() + size * 0.30,
                   size * 0.26, size * 0.20)
        )
        painter.drawLine(_norm(rect, 0.58, 0.30), _norm(rect, 0.76, 0.30))
        painter.drawLine(_norm(rect, 0.76, 0.30), _norm(rect, 0.82, 0.40))
        painter.drawLine(_norm(rect, 0.82, 0.40), _norm(rect, 0.82, 0.70))

    elif name == "door":
        path = QPainterPath()
        path.moveTo(_norm(rect, 0.30, 0.16))
        path.lineTo(_norm(rect, 0.72, 0.10))
        path.lineTo(_norm(rect, 0.78, 0.18))
        path.lineTo(_norm(rect, 0.78, 0.84))
        path.lineTo(_norm(rect, 0.30, 0.88))
        path.closeSubpath()
        painter.drawPath(path)
        painter.drawLine(_norm(rect, 0.62, 0.50), _norm(rect, 0.70, 0.50))
        painter.drawLine(_norm(rect, 0.22, 0.20), _norm(rect, 0.22, 0.84))

    elif name == "bonnet":
        path = QPainterPath()
        path.moveTo(_norm(rect, 0.18, 0.70))
        path.cubicTo(
            _norm(rect, 0.28, 0.20), _norm(rect, 0.72, 0.20),
            _norm(rect, 0.82, 0.70),
        )
        painter.drawPath(path)
        painter.drawLine(_norm(rect, 0.20, 0.80), _norm(rect, 0.80, 0.80))

    elif name == "boot":
        painter.drawRoundedRect(
            QRectF(rect.left() + size * 0.14, rect.top() + size * 0.36,
                   size * 0.72, size * 0.40),
            size * 0.10, size * 0.10,
        )
        painter.drawLine(_norm(rect, 0.30, 0.30), _norm(rect, 0.70, 0.30))
        painter.drawLine(_norm(rect, 0.50, 0.48), _norm(rect, 0.50, 0.64))

    elif name == "seatbelt":
        path = QPainterPath()
        path.moveTo(_norm(rect, 0.26, 0.20))
        path.lineTo(_norm(rect, 0.74, 0.80))
        painter.drawPath(path)
        painter.drawRoundedRect(
            QRectF(rect.left() + size * 0.60, rect.top() + size * 0.60,
                   size * 0.20, size * 0.24),
            size * 0.04, size * 0.04,
        )
        painter.drawEllipse(_norm(rect, 0.28, 0.18), size * 0.09, size * 0.09)

    elif name == "park_brake":
        painter.drawEllipse(rect.adjusted(size * 0.06, size * 0.06,
                                          -size * 0.06, -size * 0.06))
        painter.setFont(_icon_font(size * 0.46, 700))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "P")
        painter.setPen(QPen(color, width, Qt.PenStyle.SolidLine,
                            Qt.PenCapStyle.RoundCap))
        painter.drawArc(
            QRectF(rect.left() + size * 0.02, rect.top() + size * 0.02,
                   size * 0.96, size * 0.96),
            40 * 16, 100 * 16,
        )

    elif name == "tyre":
        painter.drawEllipse(rect.adjusted(size * 0.08, size * 0.08,
                                          -size * 0.08, -size * 0.08))
        painter.drawEllipse(rect.adjusted(size * 0.30, size * 0.30,
                                          -size * 0.30, -size * 0.30))
        for angle in range(0, 360, 45):
            radians = math.radians(angle)
            start = QPointF(
                rect.center().x() + math.cos(radians) * size * 0.28,
                rect.center().y() + math.sin(radians) * size * 0.28,
            )
            end = QPointF(
                rect.center().x() + math.cos(radians) * size * 0.43,
                rect.center().y() + math.sin(radians) * size * 0.43,
            )
            painter.drawLine(start, end)

    elif name == "temperature":
        painter.drawLine(_norm(rect, 0.50, 0.14), _norm(rect, 0.50, 0.64))
        painter.drawEllipse(_norm(rect, 0.50, 0.74), size * 0.17, size * 0.17)
        painter.drawLine(_norm(rect, 0.40, 0.30), _norm(rect, 0.60, 0.30))
        painter.drawLine(_norm(rect, 0.40, 0.44), _norm(rect, 0.60, 0.44))
        painter.drawLine(_norm(rect, 0.40, 0.58), _norm(rect, 0.60, 0.58))

    elif name == "oil":
        painter.drawRoundedRect(
            QRectF(rect.left() + size * 0.20, rect.top() + size * 0.28,
                   size * 0.56, size * 0.52),
            size * 0.06, size * 0.06,
        )
        painter.drawLine(_norm(rect, 0.34, 0.28), _norm(rect, 0.34, 0.16))
        painter.drawLine(_norm(rect, 0.34, 0.16), _norm(rect, 0.66, 0.16))
        painter.drawLine(_norm(rect, 0.66, 0.16), _norm(rect, 0.66, 0.28))
        path = QPainterPath()
        path.moveTo(_norm(rect, 0.48, 0.46))
        path.cubicTo(
            _norm(rect, 0.34, 0.62), _norm(rect, 0.48, 0.76),
            _norm(rect, 0.48, 0.76),
        )
        path.cubicTo(
            _norm(rect, 0.48, 0.76), _norm(rect, 0.62, 0.62),
            _norm(rect, 0.48, 0.46),
        )
        painter.drawPath(path)

    elif name == "warning":
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPolygon(_poly(rect, [(0.50, 0.10), (0.90, 0.86), (0.10, 0.86)]))
        painter.drawLine(_norm(rect, 0.50, 0.34), _norm(rect, 0.50, 0.62))
        painter.drawPoint(_norm(rect, 0.50, 0.74))

    elif name == "info":
        painter.drawEllipse(rect.adjusted(size * 0.08, size * 0.08,
                                          -size * 0.08, -size * 0.08))
        painter.drawLine(_norm(rect, 0.50, 0.42), _norm(rect, 0.50, 0.68))
        painter.drawPoint(_norm(rect, 0.50, 0.30))

    elif name == "link":
        painter.drawArc(
            QRectF(rect.left() + size * 0.12, rect.top() + size * 0.30,
                   size * 0.44, size * 0.44),
            40 * 16, 220 * 16,
        )
        painter.drawArc(
            QRectF(rect.left() + size * 0.44, rect.top() + size * 0.30,
                   size * 0.44, size * 0.44),
            220 * 16, 220 * 16,
        )
        painter.drawLine(_norm(rect, 0.36, 0.64), _norm(rect, 0.64, 0.36))

    elif name == "speed":
        painter.drawArc(
            QRectF(rect.left() + size * 0.12, rect.top() + size * 0.14,
                   size * 0.76, size * 0.76),
            225 * 16, -270 * 16,
        )
        center = _norm(rect, 0.50, 0.55)
        painter.drawLine(center, _norm(rect, 0.74, 0.28))
        painter.drawEllipse(center, size * 0.045, size * 0.045)

    elif name == "steering":
        painter.drawEllipse(rect.adjusted(size * 0.10, size * 0.10,
                                          -size * 0.10, -size * 0.10))
        painter.drawEllipse(rect.adjusted(size * 0.38, size * 0.38,
                                          -size * 0.38, -size * 0.38))
        painter.drawLine(_norm(rect, 0.50, 0.62), _norm(rect, 0.50, 0.84))
        painter.drawLine(_norm(rect, 0.50, 0.50), _norm(rect, 0.26, 0.26))
        painter.drawLine(_norm(rect, 0.50, 0.50), _norm(rect, 0.74, 0.26))

    elif name == "car":
        path = QPainterPath()
        path.moveTo(_norm(rect, 0.22, 0.72))
        path.cubicTo(
            _norm(rect, 0.22, 0.44), _norm(rect, 0.32, 0.28),
            _norm(rect, 0.50, 0.28),
        )
        path.cubicTo(
            _norm(rect, 0.68, 0.28), _norm(rect, 0.78, 0.44),
            _norm(rect, 0.78, 0.72),
        )
        painter.drawPath(path)
        painter.drawLine(_norm(rect, 0.22, 0.72), _norm(rect, 0.78, 0.72))
        painter.drawEllipse(_norm(rect, 0.33, 0.76), size * 0.07, size * 0.07)
        painter.drawEllipse(_norm(rect, 0.67, 0.76), size * 0.07, size * 0.07)

    elif name == "trip":
        painter.drawLine(_norm(rect, 0.34, 0.84), _norm(rect, 0.34, 0.30))
        painter.drawLine(_norm(rect, 0.66, 0.84), _norm(rect, 0.66, 0.30))
        painter.drawLine(_norm(rect, 0.34, 0.56), _norm(rect, 0.66, 0.56))
        painter.drawLine(_norm(rect, 0.34, 0.72), _norm(rect, 0.66, 0.72))

    elif name == "mode":
        painter.drawLine(_norm(rect, 0.16, 0.30), _norm(rect, 0.84, 0.30))
        painter.drawLine(_norm(rect, 0.16, 0.70), _norm(rect, 0.84, 0.70))
        painter.setBrush(color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(_norm(rect, 0.36, 0.30), size * 0.08, size * 0.08)
        painter.drawEllipse(_norm(rect, 0.64, 0.70), size * 0.08, size * 0.08)

    elif name == "settings":
        for y, x in ((0.28, 0.36), (0.50, 0.66), (0.72, 0.44)):
            painter.drawLine(_norm(rect, 0.16, y), _norm(rect, 0.84, y))
            painter.setBrush(color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(_norm(rect, x, y), size * 0.08, size * 0.08)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            _stroke(painter, color, rect)

    elif name == "monitor":
        painter.drawRoundedRect(
            QRectF(rect.left() + size * 0.12, rect.top() + size * 0.20,
                   size * 0.76, size * 0.60),
            size * 0.05, size * 0.05,
        )
        painter.drawLine(_norm(rect, 0.12, 0.36), _norm(rect, 0.88, 0.36))
        painter.drawLine(_norm(rect, 0.28, 0.52), _norm(rect, 0.44, 0.62))
        painter.drawLine(_norm(rect, 0.44, 0.62), _norm(rect, 0.28, 0.72))
        painter.drawLine(_norm(rect, 0.54, 0.72), _norm(rect, 0.74, 0.72))

    elif name == "close":
        painter.drawLine(_norm(rect, 0.20, 0.20), _norm(rect, 0.80, 0.80))
        painter.drawLine(_norm(rect, 0.80, 0.20), _norm(rect, 0.20, 0.80))

    elif name == "fullscreen":
        for x1, y1, x2, y2 in (
            (0.18, 0.18, 0.40, 0.18), (0.18, 0.18, 0.18, 0.40),
            (0.82, 0.18, 0.60, 0.18), (0.82, 0.18, 0.82, 0.40),
            (0.18, 0.82, 0.40, 0.82), (0.18, 0.82, 0.18, 0.60),
            (0.82, 0.82, 0.60, 0.82), (0.82, 0.82, 0.82, 0.60),
        ):
            painter.drawLine(_norm(rect, x1, y1), _norm(rect, x2, y2))

    elif name == "check":
        painter.drawLine(_norm(rect, 0.18, 0.52), _norm(rect, 0.42, 0.76))
        painter.drawLine(_norm(rect, 0.42, 0.76), _norm(rect, 0.84, 0.24))

    elif name == "abs":
        painter.drawEllipse(rect.adjusted(size * 0.06, size * 0.06,
                                          -size * 0.06, -size * 0.06))
        painter.setFont(_icon_font(size * 0.28, 700))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "ABS")

    else:
        painter.drawEllipse(rect.adjusted(size * 0.14, size * 0.14,
                                          -size * 0.14, -size * 0.14))
        painter.drawLine(_norm(rect, 0.50, 0.36), _norm(rect, 0.50, 0.66))

    painter.restore()


def _icon_font(size: float, weight: int):
    from .common import font

    return font(max(6.0, size), weight)

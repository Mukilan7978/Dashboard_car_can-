from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QColor,
    QPainter,
    QPainterPath,
    QPen,
    QTransform,
)
from PySide6.QtWidgets import QLabel

CAP_HEIGHT = 100.0
STROKE = 15.0
ADVANCE = 74.0
LEAN = 10.0

_POLYLINES: dict[str, list[tuple[list[tuple[float, float]], bool]]] = {
    "0": [([(18, 8), (43, 8), (54, 22), (54, 78), (43, 92), (18, 92),
            (7, 78), (7, 22)], True)],
    "1": [([(17, 23), (36, 7), (36, 92)], False),
          ([(18, 92), (52, 92)], False)],
    "2": [([(8, 25), (14, 11), (27, 6), (43, 6), (54, 16), (54, 31),
            (9, 83), (9, 93), (54, 93)], False)],
    "3": [([(9, 15), (21, 6), (41, 6), (53, 17), (53, 35), (43, 46),
            (53, 57), (53, 83), (41, 93), (20, 93), (9, 85)], False),
          ([(23, 46), (46, 46)], False)],
    "4": [([(45, 93), (45, 7), (8, 69), (57, 69)], False)],
    "5": [([(54, 7), (9, 7), (9, 47), (38, 47), (53, 60), (53, 82),
            (40, 93), (20, 93), (9, 85)], False)],
    "6": [([(49, 10), (36, 6), (21, 11), (10, 27), (7, 53), (7, 78),
            (18, 93), (41, 93), (53, 82), (53, 61), (41, 49), (18, 49),
            (7, 60)], False)],
    "7": [([(8, 7), (54, 7), (28, 93)], False)],
    "8": [([(18, 7), (42, 7), (51, 16), (51, 35), (42, 44), (18, 44),
            (9, 35), (9, 16)], True),
          ([(18, 56), (42, 56), (53, 66), (53, 84), (42, 93), (18, 93),
            (7, 84), (7, 66)], True)],
    "9": [([(12, 90), (24, 94), (39, 89), (50, 73), (53, 47), (53, 22),
            (42, 7), (19, 7), (7, 18), (7, 39), (19, 51), (42, 51),
            (53, 40)], False)],
    "P": [([(10, 93), (10, 7), (42, 7), (54, 19), (54, 42), (42, 54),
            (10, 54)], False)],
    "R": [([(10, 93), (10, 7), (42, 7), (54, 19), (54, 42), (42, 54),
            (10, 54)], False),
          ([(30, 54), (54, 93)], False)],
    "N": [([(10, 93), (10, 7), (54, 93), (54, 7)], False)],
    "D": [([(10, 7), (33, 7), (54, 28), (54, 72), (33, 93), (10, 93)],
            True)],
    "M": [([(8, 93), (8, 7), (31, 50), (54, 7), (54, 93)], False)],
    "G": [([(54, 20), (42, 7), (22, 7), (9, 20), (9, 80), (22, 93),
            (42, 93), (54, 80), (54, 55), (36, 55)], False)],
    "-": [([(12, 50), (50, 50)], False)],
    "+": [([(12, 50), (50, 50)], False), ([(31, 31), (31, 69)], False)],
    ".": [([(34, 87), (34, 91)], False)],
    ",": [([(34, 86), (34, 94), (27, 102)], False)],
    ":": [([(34, 35), (34, 39)], False), ([(34, 75), (34, 79)], False)],
    "/": [([(52, 7), (12, 93)], False)],
    " ": [],
}

_PUNCTUATION_ADVANCE = {".", ",", ":", " "}


def _is_supported(char: str) -> bool:
    return char in _POLYLINES or char in ("°", "%")


def is_badge_text(text: str) -> bool:
    return bool(text) and all(_is_supported(char) for char in text)


def _glyph_path(char: str) -> QPainterPath:
    path = QPainterPath()
    if char == "°":
        path.addEllipse(QRectF(20, 7, 26, 26))
        return path
    if char == "%":
        path.addEllipse(QRectF(8, 10, 22, 22))
        path.addEllipse(QRectF(38, 68, 22, 22))
        path.moveTo(54, 8)
        path.lineTo(10, 92)
        return path
    for points, closed in _POLYLINES.get(char, []):
        if not points:
            continue
        path.moveTo(QPointF(*points[0]))
        for point in points[1:]:
            path.lineTo(QPointF(*point))
        if closed:
            path.closeSubpath()
    return path


def _compose(text: str) -> QPainterPath:
    path = QPainterPath()
    x = 0.0
    for char in text:
        glyph = _glyph_path(char)
        if not glyph.isEmpty():
            path.addPath(glyph.translated(x, 0.0))
        x += 40.0 if char in _PUNCTUATION_ADVANCE else ADVANCE
    sheared = QTransform()
    sheared.shear(-LEAN / CAP_HEIGHT, 0.0)
    return sheared.map(path)


def badge_text_width(text: str, size: float) -> float:
    if not text:
        return 0.0
    bounds = _compose(text).boundingRect()
    return (bounds.width() + STROKE) * size / CAP_HEIGHT


def draw_badge_text(
    painter: QPainter,
    rect: QRectF,
    text: str,
    size: float,
    color_value: QColor,
    alignment: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignCenter,
) -> float:
    if not text or size <= 0.0:
        return 0.0
    path = _compose(text)
    bounds = path.boundingRect()
    if bounds.width() <= 0.0 and bounds.height() <= 0.0:
        return 0.0
    scale = min(
        size / CAP_HEIGHT,
        rect.width() / max(0.001, bounds.width() + STROKE),
        rect.height() / max(0.001, bounds.height() + STROKE),
    )
    if scale <= 0.0:
        return 0.0
    width = bounds.width() * scale
    height = bounds.height() * scale
    if alignment & Qt.AlignmentFlag.AlignLeft:
        target_x = rect.left()
    elif alignment & Qt.AlignmentFlag.AlignRight:
        target_x = rect.right() - width
    else:
        target_x = rect.center().x() - width / 2.0
    if alignment & Qt.AlignmentFlag.AlignTop:
        target_y = rect.top()
    elif alignment & Qt.AlignmentFlag.AlignBottom:
        target_y = rect.bottom() - height
    else:
        target_y = rect.center().y() - height / 2.0
    transform = QTransform()
    transform.translate(target_x - bounds.left() * scale,
                        target_y - bounds.top() * scale)
    transform.scale(scale, scale)

    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.setPen(QPen(
        color_value,
        max(0.8, STROKE * scale),
        Qt.PenStyle.SolidLine,
        Qt.PenCapStyle.RoundCap,
        Qt.PenJoinStyle.RoundJoin,
    ))
    painter.drawPath(transform.map(path))
    painter.restore()
    return width


class BadgeLabel(QLabel):
    def paintEvent(self, event: object) -> None:
        text = self.text()
        if not is_badge_text(text):
            super().paintEvent(event)
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        rect = QRectF(self.contentsRect())
        size = min(rect.height() * 0.78, rect.height())
        alignment = self.alignment()
        horizontal = Qt.AlignmentFlag.AlignCenter
        if alignment & Qt.AlignmentFlag.AlignLeft:
            horizontal = Qt.AlignmentFlag.AlignLeft
        elif alignment & Qt.AlignmentFlag.AlignRight:
            horizontal = Qt.AlignmentFlag.AlignRight
        vertical = Qt.AlignmentFlag.AlignVCenter
        if alignment & Qt.AlignmentFlag.AlignTop:
            vertical = Qt.AlignmentFlag.AlignTop
        elif alignment & Qt.AlignmentFlag.AlignBottom:
            vertical = Qt.AlignmentFlag.AlignBottom
        draw_badge_text(
            painter,
            rect,
            text,
            size,
            self.palette().color(self.foregroundRole()),
            horizontal | vertical,
        )
        painter.end()

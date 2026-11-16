from __future__ import annotations

from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QWidget

from dashboard.theme import Theme
from .common import color
from .icons import draw_icon


class IconTelltale(QWidget):
    def __init__(
        self,
        name: str,
        theme: Theme,
        size: int = 34,
        active_color: str | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.icon_name = name
        self.theme = theme
        self.active = False
        self.active_color = active_color
        self._size = size
        self.setFixedSize(size, size)

    def sizeHint(self) -> QSize:
        return QSize(self._size, self._size)

    def set_active(self, active: bool, active_color: str | None = None) -> None:
        changed = active != self.active or active_color != self.active_color
        self.active = bool(active)
        if active_color is not None:
            self.active_color = active_color
        if changed:
            self.update()

    def set_theme(self, theme: Theme) -> None:
        self.theme = theme
        self.update()

    def paintEvent(self, event: object) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = QRectF(self.rect()).adjusted(2, 2, -2, -2)
        if self.active:
            painter.setBrush(color(self.active_color or self.theme.accent, 30))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(rect, 9, 9)
            icon_color = color(self.active_color or self.theme.accent)
        else:
            icon_color = color(self.theme.faint, 95)
        draw_icon(painter, self.icon_name, rect.adjusted(7, 7, -7, -7), icon_color)
        painter.end()

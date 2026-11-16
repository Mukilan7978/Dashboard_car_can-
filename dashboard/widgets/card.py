from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from dashboard.theme import Theme
from .common import color
from .icons import draw_icon
from .numerals import BadgeLabel


class IconWidget(QWidget):
    def __init__(self, name: str, theme: Theme, size: int = 26,
                 icon_color: str | None = None,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.name = name
        self.theme = theme
        self.icon_color = icon_color
        self.setFixedSize(size, size)

    def set_theme(self, theme: Theme) -> None:
        self.theme = theme
        self.update()

    def paintEvent(self, event: object) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        draw_icon(
            painter,
            self.name,
            QRectF(self.rect()).adjusted(2, 2, -2, -2),
            color(self.icon_color or self.theme.accent),
        )
        painter.end()


class Card(QFrame):
    def __init__(self, theme: Theme, title: str = "", icon: str | None = None,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.theme = theme
        self.setObjectName("Card")
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(16, 13, 16, 13)
        self._layout.setSpacing(7)
        self.header = QHBoxLayout()
        self.header.setSpacing(8)
        if icon:
            self.icon = IconWidget(icon, theme, 22)
            self.header.addWidget(self.icon, 0, Qt.AlignmentFlag.AlignVCenter)
        else:
            self.icon = None
        self.title_label = QLabel(title.upper())
        self.title_label.setObjectName("CardTitle")
        self.header.addWidget(self.title_label, 1)
        self._layout.addLayout(self.header)
        self.body = QVBoxLayout()
        self.body.setSpacing(4)
        self._layout.addLayout(self.body, 1)

    def set_theme(self, theme: Theme) -> None:
        self.theme = theme
        self.setStyleSheet(self.styleSheet())
        if self.icon is not None:
            self.icon.set_theme(theme)


class MetricCard(Card):
    def __init__(self, theme: Theme, title: str, unit: str = "",
                 icon: str | None = None, detail: str = "",
                 parent: QWidget | None = None) -> None:
        super().__init__(theme, title, icon, parent)
        self.value_label = BadgeLabel("--")
        self.value_label.setObjectName("CardValue")
        self.body.addWidget(self.value_label)
        self.unit_label = QLabel(unit)
        self.unit_label.setObjectName("CardUnit")
        self.body.addWidget(self.unit_label)
        if detail:
            self.detail_label = QLabel(detail)
            self.detail_label.setObjectName("Subtle")
            self.detail_label.setWordWrap(True)
            self.body.addWidget(self.detail_label)
        else:
            self.detail_label = None
        self.body.addStretch(1)

    def set_value(self, value: str, unit: str | None = None,
                  detail: str | None = None) -> None:
        self.value_label.setText(value)
        if unit is not None:
            self.unit_label.setText(unit)
        if detail is not None and self.detail_label is not None:
            self.detail_label.setText(detail)

    def set_tint(self, tint: str | None) -> None:
        if tint:
            self.value_label.setStyleSheet(f"color: {tint};")
        else:
            self.value_label.setStyleSheet("")

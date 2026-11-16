from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QTimer, Qt
from PySide6.QtWidgets import QGraphicsOpacityEffect, QLabel, QWidget

from dashboard.theme import Theme


class Toast(QLabel):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setVisible(False)
        self._effect = QGraphicsOpacityEffect(self)
        self._effect.setOpacity(0.0)
        self.setGraphicsEffect(self._effect)
        self._fade = QPropertyAnimation(self._effect, b"opacity", self)
        self._fade.setDuration(160)
        self._fade.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self._fade_out)

    def show_message(self, text: str, level: str, theme: Theme) -> None:
        tint = {
            "ok": theme.green,
            "warn": theme.amber,
            "error": theme.red,
        }.get(level, theme.accent)
        self.setText(text)
        self.setStyleSheet(
            f"QLabel {{"
            f" background-color: rgba(5, 10, 18, 238);"
            f" color: {tint};"
            f" border: 1px solid {tint};"
            f" border-radius: 14px;"
            f" padding: 9px 22px;"
            f" font-family: 'Lato'; font-size: 12px;"
            f" font-weight: 800; letter-spacing: 2px;"
            f"}}"
        )
        self.adjustSize()
        self._reposition()
        self.raise_()
        self.show()
        self._fade.stop()
        self._fade.setStartValue(self._effect.opacity())
        self._fade.setEndValue(1.0)
        self._fade.start()
        self._hide_timer.start(1900)

    def _fade_out(self) -> None:
        self._fade.stop()
        self._fade.setStartValue(self._effect.opacity())
        self._fade.setEndValue(0.0)
        self._fade.finished.connect(self._finish_hide)
        self._fade.start()

    def _finish_hide(self) -> None:
        try:
            self._fade.finished.disconnect(self._finish_hide)
        except RuntimeError:
            pass
        if self._effect.opacity() <= 0.01:
            self.hide()

    def _reposition(self) -> None:
        parent = self.parentWidget()
        if parent is None:
            return
        self.move(
            max(8, (parent.width() - self.width()) // 2),
            78,
        )

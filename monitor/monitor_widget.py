from __future__ import annotations

import html
from collections import deque
from datetime import datetime

from PySide6.QtCore import QTimer, Signal, Qt
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from can_bus.can_decoder import DecodedFrame
from dashboard.theme import Theme


class CanMonitorWidget(QWidget):
    close_requested = Signal()

    def __init__(self, theme: Theme, channel: str = "vcan0",
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.theme = theme
        self.channel = channel
        self.link = False
        self.paused = False
        self.active = False
        self.frames: deque[DecodedFrame] = deque(maxlen=4000)
        self.pending: deque[DecodedFrame] = deque(maxlen=1000)
        self.total = 0
        self.invalid = 0
        self._link_text = ""
        self._link_tint = ""

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(8)

        header = QHBoxLayout()
        header.setSpacing(10)
        title = QLabel("CAN MONITOR")
        title.setObjectName("SectionTitle")
        header.addWidget(title)
        self.channel_label = QLabel(f"CHANNEL  {self.channel.upper()}")
        self.channel_label.setObjectName("CardTitle")
        header.addWidget(self.channel_label)
        self.link_label = QLabel("OFFLINE")
        self.link_label.setObjectName("Accent")
        header.addWidget(self.link_label)
        header.addStretch(1)
        self.count_label = QLabel("FRAMES  0     INVALID  0")
        self.count_label.setObjectName("Subtle")
        header.addWidget(self.count_label)
        self.close_button = QPushButton("CLOSE  [F12]")
        self.close_button.clicked.connect(self.close_requested.emit)
        header.addWidget(self.close_button)
        root.addLayout(header)

        controls = QHBoxLayout()
        controls.setSpacing(8)
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText(
            "Filter by CAN ID, name, source, value, or data bytes…"
        )
        self.filter_edit.textChanged.connect(self._rebuild)
        controls.addWidget(self.filter_edit, 1)
        self.pause_button = QPushButton("PAUSE")
        self.pause_button.setCheckable(True)
        self.pause_button.toggled.connect(self._set_paused)
        controls.addWidget(self.pause_button)
        self.clear_button = QPushButton("CLEAR")
        self.clear_button.clicked.connect(self._clear)
        controls.addWidget(self.clear_button)
        root.addLayout(controls)

        self.text = QTextEdit()
        self.text.setReadOnly(True)
        self.text.setAcceptRichText(True)
        self.text.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.text.document().setMaximumBlockCount(3000)
        self.text.setObjectName("CanTerminal")
        root.addWidget(self.text, 1)

        self.footer = QLabel(
            "Raw SocketCAN frames decoded with the project message catalogue. "
            "F12 toggles this terminal."
        )
        self.footer.setObjectName("Subtle")
        root.addWidget(self.footer)

        self._timer = QTimer(self)
        self._timer.setInterval(100)
        self._timer.timeout.connect(self._flush)
        self.set_theme(theme)

    def set_active(self, active: bool) -> None:
        if active == self.active:
            return
        self.active = active
        if active:
            self._rebuild()
            self._timer.start()
        else:
            self._timer.stop()
            self.pending.clear()

    def set_channel(self, channel: str) -> None:
        self.channel = channel
        self.channel_label.setText(f"CHANNEL  {channel.upper()}")

    def set_theme(self, theme: Theme) -> None:
        self.theme = theme
        self.channel_label.setStyleSheet(f"color: {theme.muted};")
        self.footer.setStyleSheet(f"color: {theme.muted};")
        self.text.setStyleSheet(
            f"QTextEdit#CanTerminal {{"
            f" background-color: #03060A; color: {theme.text};"
            f" border: 1px solid {theme.border}; border-radius: 10px;"
            f" padding: 8px; font-family: 'DejaVu Sans Mono', monospace;"
            f" font-size: 11px; }}"
        )
        self._link_tint = ""
        self.set_link(self.link, self._link_text)

    def set_link(self, link: bool, text: str = "") -> None:
        label = text or self._link_text or self.channel
        tint = self.theme.green if link else self.theme.red
        if link == self.link and label == self._link_text and tint == self._link_tint:
            return
        self.link = link
        self._link_text = label
        self._link_tint = tint
        self.link_label.setText("LINKED" if link else "OFFLINE")
        self.link_label.setStyleSheet(
            f"color: {tint}; font-weight: 700; font-size: 11px;"
        )
        self.channel_label.setText(f"CHANNEL  {label.upper()}")

    def append_frame(self, frame: DecodedFrame) -> None:
        self.total += 1
        if not frame.valid:
            self.invalid += 1
        self.frames.append(frame)
        if self.paused or not self.active:
            return
        self.pending.append(frame)

    def _set_paused(self, paused: bool) -> None:
        self.paused = paused
        self.pause_button.setText("RESUME" if paused else "PAUSE")
        if not paused:
            self._rebuild()
            self.pending.clear()

    def _matches(self, frame: DecodedFrame) -> bool:
        query = self.filter_edit.text().strip().lower()
        if not query:
            return True
        haystack = " ".join((
            frame.id_hex,
            frame.name,
            frame.source,
            frame.data_hex,
            frame.summary(),
            frame.error or "",
        )).lower()
        return query in haystack

    def _format_html(self, frame: DecodedFrame) -> str:
        timestamp = datetime.fromtimestamp(frame.timestamp).strftime("%H:%M:%S.%f")[:-3]
        if not frame.valid:
            tint = self.theme.amber
            suffix = f"  !! {frame.error}" if frame.error else "  !!"
        else:
            tint = self.theme.text
            suffix = ""
        line = (
            f"{timestamp}   {frame.id_hex}   "
            f"[{frame.dlc}]  {frame.data_hex:<24} "
            f"{frame.source:<12} {frame.name:<24} {frame.summary()}{suffix}"
        )
        return (
            f'<span style="color:{tint};">{html.escape(line)}</span>'
        )

    def _append_line(self, frame: DecodedFrame) -> None:
        self.text.moveCursor(QTextCursor.MoveOperation.End)
        self.text.insertHtml(self._format_html(frame) + "<br>")
        self.text.moveCursor(QTextCursor.MoveOperation.End)

    def _rebuild(self) -> None:
        self.text.clear()
        matching = [frame for frame in self.frames if self._matches(frame)]
        for frame in matching[-250:]:
            self._append_line(frame)
        if len(matching) > 250:
            self.text.moveCursor(QTextCursor.MoveOperation.Start)
            self.text.insertHtml(
                f'<span style="color:{self.theme.muted};">'
                f"— showing last 250 of {len(matching)} matching frames —"
                "</span><br>"
            )
        self.text.moveCursor(QTextCursor.MoveOperation.End)
        self._update_counts()

    def _clear(self) -> None:
        self.frames.clear()
        self.pending.clear()
        self.text.clear()
        self.total = 0
        self.invalid = 0
        self._update_counts()

    def _flush(self) -> None:
        if not self.active:
            self.pending.clear()
            return
        if self.paused:
            self.pending.clear()
            return
        if self.pending:
            pending = list(self.pending)
            self.pending.clear()
            if len(pending) > 300:
                pending = pending[-300:]
            scrollbar = self.text.verticalScrollBar()
            at_bottom = scrollbar.value() >= scrollbar.maximum() - 8
            for frame in pending:
                if self._matches(frame):
                    self._append_line(frame)
            if at_bottom:
                self.text.moveCursor(QTextCursor.MoveOperation.End)
                scrollbar.setValue(scrollbar.maximum())
        self._update_counts()

    def _update_counts(self) -> None:
        self.count_label.setText(
            f"FRAMES  {self.total:,}     INVALID  {self.invalid:,}"
        )

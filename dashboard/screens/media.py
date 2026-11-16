from __future__ import annotations

import time

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QProgressBar,
    QPushButton,
    QSlider,
    QVBoxLayout,
)

from dashboard.theme import Theme
from dashboard.widgets.album_art import AlbumArt
from dashboard.widgets.card import Card
from .base import BaseScreen


class MediaScreen(BaseScreen):
    TRACKS = (
        ("Midnight Drive", "AutoSim Sessions", "4:12", 252),
        ("Electric Skyline", "Neon Circuit", "3:48", 228),
        ("Carbon Weave", "AutoSim Sessions", "5:06", 306),
        ("Afterglow", "Vector Fields", "4:27", 267),
        ("Coastal Route", "AutoSim Sessions", "3:36", 216),
        ("Telemetry", "Neon Circuit", "6:02", 362),
    )

    def __init__(self, theme: Theme) -> None:
        super().__init__(theme)
        root = QHBoxLayout(self)
        root.setContentsMargins(18, 14, 18, 14)
        root.setSpacing(12)

        art_card = Card(theme, "Now playing", "mode")
        self.album = AlbumArt(theme)
        art_card.body.addWidget(self.album, 1)
        self.album_title = QLabel("SYNTHETIC ROADS")
        self.album_title.setObjectName("SectionTitle")
        art_card.body.addWidget(self.album_title)
        self.album_subtitle = QLabel("AutoSim Sessions · 2026 · Simulated")
        self.album_subtitle.setObjectName("Subtle")
        art_card.body.addWidget(self.album_subtitle)
        root.addWidget(art_card, 4)

        right = QVBoxLayout()
        right.setSpacing(10)

        player = Card(theme, "Player", "mode")
        self.track_title = QLabel()
        self.track_title.setObjectName("SectionTitle")
        self.track_title.setStyleSheet("font-size: 26px;")
        player.body.addWidget(self.track_title)
        self.artist_label = QLabel()
        self.artist_label.setObjectName("Accent")
        player.body.addWidget(self.artist_label)
        self.album_label = QLabel("Synthetic Roads · Simulated media")
        self.album_label.setObjectName("Subtle")
        player.body.addWidget(self.album_label)

        progress_row = QHBoxLayout()
        self.elapsed_label = QLabel("0:00")
        self.elapsed_label.setObjectName("Subtle")
        self.progress = QProgressBar()
        self.progress.setRange(0, 1000)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(8)
        self.duration_label = QLabel("0:00")
        self.duration_label.setObjectName("Subtle")
        progress_row.addWidget(self.elapsed_label)
        progress_row.addWidget(self.progress, 1)
        progress_row.addWidget(self.duration_label)
        player.body.addLayout(progress_row)

        controls = QHBoxLayout()
        controls.setSpacing(8)
        self.prev_button = QPushButton("PREV")
        self.play_button = QPushButton("PAUSE")
        self.play_button.setObjectName("Primary")
        self.next_button = QPushButton("NEXT")
        self.prev_button.clicked.connect(self._previous)
        self.play_button.clicked.connect(self._toggle_play)
        self.next_button.clicked.connect(self._next)
        controls.addStretch(1)
        controls.addWidget(self.prev_button)
        controls.addWidget(self.play_button)
        controls.addWidget(self.next_button)
        controls.addStretch(1)
        player.body.addLayout(controls)

        volume_row = QHBoxLayout()
        volume_label = QLabel("VOLUME")
        volume_label.setObjectName("CardTitle")
        self.volume = QSlider(Qt.Orientation.Horizontal)
        self.volume.setRange(0, 100)
        self.volume.setValue(62)
        self.volume_value = QLabel("62")
        self.volume_value.setObjectName("Subtle")
        self.volume.valueChanged.connect(
            lambda value: self.volume_value.setText(str(value))
        )
        volume_row.addWidget(volume_label)
        volume_row.addWidget(self.volume, 1)
        volume_row.addWidget(self.volume_value)
        player.body.addLayout(volume_row)

        disclaimer = QLabel(
            "SIMULATED MEDIA — NO AUDIO OUTPUT. This screen demonstrates the "
            "cockpit UI only."
        )
        disclaimer.setObjectName("Subtle")
        disclaimer.setWordWrap(True)
        disclaimer.setStyleSheet(f"color: {theme.amber}; font-size: 10px;")
        player.body.addWidget(disclaimer)
        right.addWidget(player, 0)

        playlist_card = Card(theme, "Playlist", "monitor")
        self.playlist = QListWidget()
        for title, artist, duration, _seconds in self.TRACKS:
            self.playlist.addItem(f"{title}    ·    {artist}    ·    {duration}")
        self.playlist.setCurrentRow(0)
        self.playlist.currentRowChanged.connect(self._row_changed)
        playlist_card.body.addWidget(self.playlist, 1)
        right.addWidget(playlist_card, 1)
        root.addLayout(right, 6)

        self.track_index = 0
        self.playing = True
        self.position_s = 0.0
        self._last = time.monotonic()
        self._load_track(0)

    def _format_time(self, seconds: float) -> str:
        total = int(max(0, seconds))
        return f"{total // 60}:{total % 60:02d}"

    def _load_track(self, index: int) -> None:
        index = index % len(self.TRACKS)
        self.track_index = index
        title, artist, _duration, seconds = self.TRACKS[index]
        self.position_s = 0.0
        self.track_title.setText(title)
        self.artist_label.setText(artist)
        self.duration_label.setText(self._format_time(seconds))
        self.progress.setValue(0)
        if self.playlist.currentRow() != index:
            self.playlist.blockSignals(True)
            self.playlist.setCurrentRow(index)
            self.playlist.blockSignals(False)

    def _row_changed(self, index: int) -> None:
        if index >= 0:
            self._load_track(index)
            self.playing = True
            self.play_button.setText("PAUSE")

    def _toggle_play(self) -> None:
        self.playing = not self.playing
        self.play_button.setText("PAUSE" if self.playing else "PLAY")

    def _previous(self) -> None:
        self._load_track(self.track_index - 1)

    def _next(self) -> None:
        self._load_track(self.track_index + 1)

    def refresh(self) -> None:
        now = time.monotonic()
        dt = min(0.2, max(0.0, now - self._last))
        self._last = now
        if not self.playing:
            return
        _title, _artist, _duration, seconds = self.TRACKS[self.track_index]
        self.position_s += dt
        if self.position_s >= seconds:
            self._load_track(self.track_index + 1)
            return
        self.elapsed_label.setText(self._format_time(self.position_s))
        self.progress.setValue(int(1000 * self.position_s / seconds))

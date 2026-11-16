from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout

from dashboard.theme import Theme
from dashboard.widgets.arc_gauge import Speedometer, Tachometer
from dashboard.widgets.cluster_center import ClusterCenter
from dashboard.widgets.common import AnimatedValue, clamp
from dashboard.widgets.metric_strip import MetricStrip
from .base import BaseScreen


class CockpitScreen(BaseScreen):
    def __init__(self, theme: Theme) -> None:
        super().__init__(theme)
        self._root = QVBoxLayout(self)
        self._root.setContentsMargins(18, 12, 18, 12)
        self._root.setSpacing(10)

        self._cluster = QHBoxLayout()
        self._cluster.setSpacing(12)
        self.speedometer = Speedometer(theme)
        self.cluster_center = ClusterCenter(theme)
        self.tachometer = Tachometer(theme)
        self._cluster.addWidget(self.speedometer, 5)
        self._cluster.addWidget(self.cluster_center, 4)
        self._cluster.addWidget(self.tachometer, 5)
        self._root.addLayout(self._cluster, 1)

        self.metrics = MetricStrip(theme)
        self._root.addWidget(self.metrics, 0)

        self.cluster_center.engine_toggle.connect(
            lambda: self.send("engine_toggle")
        )

        self._speed_anim = AnimatedValue(0.0, speed=8.0)
        self._rpm_anim = AnimatedValue(0.0, speed=10.0)
        self._initialised = False
        self._last_speed: float = 0.0
        self._last_rpm: float = 0.0

    def resizeEvent(self, event: object) -> None:
        super().resizeEvent(event)
        window = self.window()
        width = window.width() if window is not None else self.width()
        height = window.height() if window is not None else self.height()
        scale = clamp(min(width / 1600.0, height / 900.0), 0.75, 2.6)
        self._root.setContentsMargins(
            round(18 * scale), round(12 * scale),
            round(18 * scale), round(12 * scale),
        )
        self._root.setSpacing(max(2, round(10 * scale)))
        self._cluster.setSpacing(max(2, round(12 * scale)))
        self.metrics.setFixedHeight(max(60, round(100 * scale)))
        self.cluster_center.set_scale(scale)

    def refresh(self) -> None:
        snapshot = self.snapshot
        if snapshot is None:
            return
        if not self._initialised:
            self._speed_anim.snap(snapshot.speed_abs if snapshot.link else 0.0)
            self._rpm_anim.snap(snapshot.rpm if snapshot.link else 0.0)
            self._initialised = True
        # Only update animations if values changed significantly
        speed_changed = abs(snapshot.speed_abs - self._last_speed) > 0.5
        rpm_changed = abs(snapshot.rpm - self._last_rpm) > 2.0
        if speed_changed:
            self._last_speed = snapshot.speed_abs
            self._speed_anim.set_target(snapshot.speed_abs if snapshot.link else 0.0)
        if rpm_changed:
            self._last_rpm = snapshot.rpm
            self._rpm_anim.set_target(snapshot.rpm if snapshot.link else 0.0)
        self.speedometer.set_value(self._speed_anim.update(), snapshot.link)
        self.tachometer.set_value(self._rpm_anim.update(), snapshot.link)
        self.cluster_center.set_snapshot(snapshot)
        self.metrics.set_snapshot(snapshot)

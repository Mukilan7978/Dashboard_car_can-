from __future__ import annotations

import json
import threading
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import can

from config.settings import SECURITY_LOG_MAX_BYTES
from .can_decoder import DecodedFrame
from .message_definitions import BY_ID


@dataclass
class SecurityEvent:
    kind: str
    severity: str
    message: str
    can_id: int | None
    timestamp: float


class SecurityMonitor:
    def __init__(self, path: Path | None = None) -> None:
        self.path = Path(path) if path else None
        if self.path is not None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._windows: dict[int, deque[float]] = {}
        self._last_event: dict[tuple[str, int | None], float] = {}
        self.events: deque[SecurityEvent] = deque(maxlen=200)
        if self.path is not None and not self.path.exists():
            self.path.write_text("", encoding="utf-8")

    def _emit(self, kind: str, severity: str, message: str, can_id: int | None) -> None:
        now = time.monotonic()
        key = (kind, can_id)
        if now - self._last_event.get(key, 0.0) < 1.0:
            return
        self._last_event[key] = now
        event = SecurityEvent(kind, severity, message, can_id, time.time())
        self.events.append(event)
        self._write(event)

    def _write(self, event: SecurityEvent) -> None:
        if self.path is None:
            return
        with self._lock:
            try:
                if self.path.stat().st_size > SECURITY_LOG_MAX_BYTES:
                    stamp = time.strftime("%Y%m%d-%H%M%S")
                    rotated = self.path.with_name(
                        f"{self.path.stem}-{stamp}{self.path.suffix}"
                    )
                    self.path.rename(rotated)
            except OSError:
                pass
            record: dict[str, Any] = {
                "timestamp": event.timestamp,
                "kind": event.kind,
                "severity": event.severity,
                "can_id": f"0x{event.can_id:03X}" if event.can_id is not None else None,
                "message": event.message,
            }
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, ensure_ascii=True) + "\n")

    def observe(self, message: can.Message, decoded: DecodedFrame | None) -> None:
        can_id = message.arbitration_id
        now = time.monotonic()
        window = self._windows.setdefault(can_id, deque(maxlen=400))
        window.append(now)
        while window and now - window[0] > 1.0:
            window.popleft()
        spec = BY_ID.get(can_id)
        if spec is None:
            self._emit("unknown_id", "warning",
                       f"Unknown CAN ID 0x{can_id:03X}", can_id)
            return
        expected = 1000.0 / spec.period_ms
        if len(window) > expected * 2.2 + 8:
            self._emit("rate_anomaly", "warning",
                       f"0x{can_id:03X} rate {len(window)}/s exceeds {expected:.0f} Hz",
                       can_id)
        if decoded is not None and not decoded.valid:
            self._emit("invalid_frame", "warning",
                       f"0x{can_id:03X}: {decoded.error}", can_id)

    def note(self, kind: str, message: str, severity: str = "info",
             can_id: int | None = None) -> None:
        self._emit(kind, severity, message, can_id)

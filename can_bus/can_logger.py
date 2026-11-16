from __future__ import annotations

import csv
import threading
import time
from pathlib import Path
from typing import Any

import can

from config.settings import CAN_LOG_MAX_BYTES
from .can_decoder import DecodedFrame


class CanLogger:
    def __init__(self, path: Path, max_bytes: int = CAN_LOG_MAX_BYTES) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.max_bytes = max_bytes
        self._lock = threading.Lock()
        self._file = self.path.open("a", newline="", encoding="utf-8")
        self._writer = csv.writer(self._file)
        if self._file.tell() == 0:
            self._writer.writerow(
                ["wall_time", "can_id", "source", "name", "dlc", "data", "decoded"]
            )
            self._file.flush()

    def _rotate_if_needed(self) -> None:
        try:
            size = self.path.stat().st_size
        except OSError:
            return
        if size < self.max_bytes:
            return
        self._file.close()
        stamp = time.strftime("%Y%m%d-%H%M%S")
        rotated = self.path.with_name(f"{self.path.stem}-{stamp}{self.path.suffix}")
        try:
            self.path.rename(rotated)
        except OSError:
            pass
        self._file = self.path.open("a", newline="", encoding="utf-8")
        self._writer = csv.writer(self._file)
        self._writer.writerow(
            ["wall_time", "can_id", "source", "name", "dlc", "data", "decoded"]
        )

    def log_message(self, message: can.Message, decoded: DecodedFrame | None = None) -> None:
        with self._lock:
            self._rotate_if_needed()
            self._writer.writerow(
                [
                    f"{time.time():.6f}",
                    f"0x{message.arbitration_id:03X}",
                    decoded.source if decoded else "UNKNOWN",
                    decoded.name if decoded else "UNKNOWN",
                    message.dlc,
                    " ".join(f"{byte:02X}" for byte in message.data),
                    decoded.summary() if decoded else "",
                ]
            )
            self._file.flush()

    def log_event(self, kind: str, message: str, can_id: int | None = None,
                  severity: str = "info", **extra: Any) -> None:
        with self._lock:
            self._rotate_if_needed()
            self._writer.writerow(
                [
                    f"{time.time():.6f}",
                    f"0x{can_id:03X}" if can_id is not None else "",
                    f"EVENT:{kind}",
                    severity,
                    "",
                    "",
                    message,
                ]
            )
            self._file.flush()

    def close(self) -> None:
        with self._lock:
            try:
                self._file.close()
            except OSError:
                pass

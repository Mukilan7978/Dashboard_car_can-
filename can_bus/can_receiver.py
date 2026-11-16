from __future__ import annotations

import time

import can

from config import can_config
from .can_manager import open_bus


class CanReceiver:
    def __init__(self, channel: str, interface: str, bus: can.BusABC | None = None) -> None:
        self.channel = channel
        self.interface = interface
        self.bus = bus or open_bus(channel, interface)
        self.errors = 0

    def recv(self, timeout: float = can_config.RECEIVE_TIMEOUT_S) -> can.Message | None:
        try:
            return self.bus.recv(timeout=timeout)
        except can.CanError:
            self.errors += 1
            return None

    def close(self) -> None:
        try:
            self.bus.shutdown()
        except can.CanError:
            pass


class ReconnectingReceiver:
    def __init__(self, channel: str, interface: str) -> None:
        self.channel = channel
        self.interface = interface
        self.bus: can.BusABC | None = None
        self.errors = 0
        self._last_attempt = 0.0

    def _ensure_bus(self) -> bool:
        if self.bus is not None:
            return True
        now = time.monotonic()
        if now - self._last_attempt < can_config.SOCKETCAN_ERROR_RETRY_S:
            return False
        self._last_attempt = now
        try:
            self.bus = open_bus(self.channel, self.interface)
            return True
        except (OSError, can.CanError):
            self.errors += 1
            return False

    def recv(self, timeout: float = can_config.RECEIVE_TIMEOUT_S) -> can.Message | None:
        if not self._ensure_bus():
            time.sleep(min(timeout, 0.05))
            return None
        try:
            return self.bus.recv(timeout=timeout)  # type: ignore[union-attr]
        except can.CanError:
            self.errors += 1
            self.close()
            return None

    def close(self) -> None:
        if self.bus is not None:
            try:
                self.bus.shutdown()
            except can.CanError:
                pass
            self.bus = None

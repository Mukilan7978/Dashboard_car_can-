from __future__ import annotations

import threading
from typing import Callable

import can

from .can_manager import open_bus

Validator = Callable[[can.Message], tuple[bool, str]]


class CanSender:
    def __init__(
        self,
        channel: str,
        interface: str,
        validator: Validator | None = None,
        bus: can.BusABC | None = None,
    ) -> None:
        self.channel = channel
        self.interface = interface
        self.validator = validator
        self.bus = bus or open_bus(channel, interface)
        self._lock = threading.Lock()
        self.sent = 0
        self.rejected = 0
        self.errors = 0

    def send(self, message: can.Message) -> bool:
        if self.validator is not None:
            ok, _reason = self.validator(message)
            if not ok:
                self.rejected += 1
                return False
        with self._lock:
            try:
                self.bus.send(message)
            except can.CanError:
                self.errors += 1
                return False
        self.sent += 1
        return True

    def close(self) -> None:
        try:
            self.bus.shutdown()
        except can.CanError:
            pass

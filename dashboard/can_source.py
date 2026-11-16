from __future__ import annotations

import threading

from PySide6.QtCore import QThread, Signal

import can

from can_bus.can_decoder import DecodedFrame, decode_message
from can_bus.can_manager import open_bus


class CanBusSource(QThread):
    frame_received = Signal(object)
    link_changed = Signal(bool, str)

    def __init__(self, channel: str, interface: str, parent: object | None = None) -> None:
        super().__init__(parent)
        self.channel = channel
        self.interface = interface
        self._stop = threading.Event()
        self._bus: can.BusABC | None = None

    def run(self) -> None:
        try:
            self._bus = open_bus(self.channel, self.interface)
        except Exception as error:
            self.link_changed.emit(False, str(error))
            return
        self.link_changed.emit(True, f"{self.interface}:{self.channel}")
        bus = self._bus
        while not self._stop.is_set():
            try:
                message = bus.recv(timeout=0.2)
            except Exception as error:
                self.link_changed.emit(False, str(error))
                break
            if message is None:
                continue
            decoded: DecodedFrame = decode_message(message)
            self.frame_received.emit(decoded)
        try:
            bus.shutdown()
        except Exception:
            pass
        self._bus = None
        self.link_changed.emit(False, "bus closed")

    def stop(self) -> None:
        self._stop.set()

    def send(self, message: can.Message) -> bool:
        if self._bus is None:
            return False
        try:
            self._bus.send(message)
            return True
        except Exception:
            return False

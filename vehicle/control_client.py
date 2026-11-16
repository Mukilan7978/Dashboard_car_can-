from __future__ import annotations

import queue
import socket
import threading
import time
from pathlib import Path
from typing import Any

from .control_protocol import encode_command


class ControlClient:
    def __init__(self, path: Path, max_queue: int = 200) -> None:
        self.path = str(path)
        self._queue: queue.Queue[dict[str, Any]] = queue.Queue(maxsize=max_queue)
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, name="ControlClient", daemon=True)
        self._connected = False
        self._lock = threading.Lock()

    @property
    def connected(self) -> bool:
        with self._lock:
            return self._connected

    def start(self) -> None:
        if not self._thread.is_alive():
            self._thread.start()

    def send(self, command: dict[str, Any]) -> bool:
        try:
            self._queue.put_nowait(command)
            return True
        except queue.Full:
            return False

    def stop(self) -> None:
        self._stop.set()
        if self._thread.is_alive():
            self._thread.join(timeout=1.5)

    def _set_connected(self, value: bool) -> None:
        with self._lock:
            self._connected = value

    def _drain(self) -> None:
        while True:
            try:
                self._queue.get_nowait()
            except queue.Empty:
                return

    def _run(self) -> None:
        sock: socket.socket | None = None
        while not self._stop.is_set():
            if sock is None:
                try:
                    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                    sock.settimeout(0.5)
                    sock.connect(self.path)
                    self._set_connected(True)
                except OSError:
                    if sock is not None:
                        try:
                            sock.close()
                        except OSError:
                            pass
                    sock = None
                    self._set_connected(False)
                    self._drain()
                    time.sleep(0.4)
                    continue
            try:
                command = self._queue.get(timeout=0.1)
            except queue.Empty:
                continue
            try:
                sock.sendall(encode_command(command))
            except OSError:
                try:
                    sock.close()
                except OSError:
                    pass
                sock = None
                self._set_connected(False)
                self._drain()
        if sock is not None:
            try:
                sock.close()
            except OSError:
                pass
        self._set_connected(False)

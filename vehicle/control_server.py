from __future__ import annotations

import os
import queue
import socketserver
from pathlib import Path
from typing import Any

from .control_protocol import decode_command, encode_command


class _ControlHandler(socketserver.StreamRequestHandler):
    def handle(self) -> None:
        for raw in self.rfile:
            command = decode_command(raw)
            if command is None:
                continue
            if command.get("cmd") == "ping":
                try:
                    self.wfile.write(encode_command({"ok": True}))
                    self.wfile.flush()
                except OSError:
                    pass
                continue
            self.server.command_queue.put(command)  # type: ignore[attr-defined]

    def finish(self) -> None:
        try:
            self.server.command_queue.put({"cmd": "release_all"})  # type: ignore[attr-defined]
        except Exception:
            pass
        super().finish()


class ControlServer(socketserver.ThreadingMixIn, socketserver.UnixStreamServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, path: Path, command_queue: queue.Queue[dict[str, Any]]) -> None:
        self.command_queue = command_queue
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass
        super().__init__(str(self.path), _ControlHandler)
        try:
            os.chmod(self.path, 0o600)
        except OSError:
            pass

    def close(self) -> None:
        try:
            self.shutdown()
        except Exception:
            pass
        try:
            self.server_close()
        except Exception:
            pass
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass

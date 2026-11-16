from __future__ import annotations

import argparse
import json
import os
import socket
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.settings import CONTROL_SOCKET  # noqa: E402


def send(sock: socket.socket, payload: dict) -> None:
    data = (json.dumps(payload, separators=(",", ":")) + "\n").encode("utf-8")
    sock.sendall(data)
    print("sent:", json.dumps(payload, separators=(",", ":")))


def parse_line(line: str) -> dict | None:
    line = line.strip()
    if not line:
        return None
    if line.startswith("{"):
        try:
            value = json.loads(line)
        except json.JSONDecodeError as error:
            print(f"invalid JSON: {error}")
            return None
        return value if isinstance(value, dict) else None
    parts = line.split()
    if parts[0] == "input" and len(parts) >= 3:
        value_text = " ".join(parts[2:])
        try:
            value: object = json.loads(value_text)
        except json.JSONDecodeError:
            value = value_text
        return {"cmd": "input", "name": parts[1], "value": value}
    if parts[0] in ("mode_set", "steering_setting", "set_gear", "indicator",
                    "light_toggle", "door_toggle", "mirror_toggle"):
        if len(parts) >= 2:
            return {"cmd": parts[0], "value": " ".join(parts[1:])}
    return {"cmd": parts[0]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Send JSON-lines commands to the simulator control socket"
    )
    parser.add_argument(
        "--socket",
        default=os.environ.get("AUTODASH_CONTROL_SOCKET", str(CONTROL_SOCKET)),
    )
    parser.add_argument(
        "--hold",
        type=float,
        default=0.0,
        metavar="SECONDS",
        help="Keep the connection open after a one-shot command (useful for "
             "held inputs such as throttle).",
    )
    parser.add_argument(
        "command",
        nargs="*",
        help="JSON object or simple command. Omit to enter interactive mode.",
    )
    args = parser.parse_args(argv)

    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        sock.connect(args.socket)
    except OSError as error:
        print(f"cannot connect to {args.socket}: {error}", file=sys.stderr)
        return 1

    try:
        if args.command:
            line = " ".join(args.command)
            command = parse_line(line)
            if command is not None:
                send(sock, command)
            if args.hold > 0:
                time.sleep(args.hold)
            return 0
        print(f"connected to {args.socket}")
        print("enter JSON or commands such as: gear_cycle_mode, mode_set SPORT, "
              "input throttle 1")
        for line in sys.stdin:
            command = parse_line(line)
            if command is None:
                continue
            if command.get("cmd") in ("quit", "exit"):
                break
            send(sock, command)
    except (BrokenPipeError, ConnectionResetError):
        print("simulator disconnected", file=sys.stderr)
        return 1
    finally:
        sock.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

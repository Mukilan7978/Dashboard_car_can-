from __future__ import annotations

import json
from typing import Any


def encode_command(command: dict[str, Any]) -> bytes:
    return (json.dumps(command, separators=(",", ":")) + "\n").encode("utf-8")


def decode_command(raw: bytes) -> dict[str, Any] | None:
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def input_command(name: str, value: Any) -> dict[str, Any]:
    return {"cmd": "input", "name": name, "value": value}


def simple_command(name: str) -> dict[str, Any]:
    return {"cmd": name}


def value_command(name: str, value: Any) -> dict[str, Any]:
    return {"cmd": name, "value": value}

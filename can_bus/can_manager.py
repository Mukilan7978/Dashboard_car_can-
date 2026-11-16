from __future__ import annotations

import shutil
import subprocess
from typing import Any

import can

from config import can_config


def interface_exists(channel: str, interface: str = can_config.DEFAULT_INTERFACE) -> bool:
    if interface == "virtual":
        return True
    if interface != "socketcan":
        return True
    try:
        result = subprocess.run(
            ["ip", "link", "show", channel],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0


def interface_is_up(channel: str) -> bool:
    try:
        result = subprocess.run(
            ["ip", "link", "show", channel],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    if result.returncode != 0:
        return False
    first_line = result.stdout.splitlines()[0] if result.stdout else ""
    return "<" in first_line and "UP" in first_line.split("<", 1)[1].split(">", 1)[0]


def can_utils_available() -> bool:
    return shutil.which("candump") is not None and shutil.which("cansend") is not None


def open_bus(channel: str, interface: str, **kwargs: Any) -> can.BusABC:
    return can.interface.Bus(channel=channel, interface=interface, **kwargs)


def describe_link(channel: str, interface: str) -> str:
    if interface == "virtual":
        return f"virtual:{channel}"
    if not interface_exists(channel, interface):
        return f"{channel}: missing"
    return f"{channel}: {'up' if interface_is_up(channel) else 'down'}"

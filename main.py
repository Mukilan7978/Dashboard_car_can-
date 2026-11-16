from __future__ import annotations

import argparse
import os
import sys


from config import can_config
from config.settings import CONTROL_SOCKET
from dashboard.app import run


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="AUTOSIM automotive cockpit dashboard"
    )
    parser.add_argument(
        "--channel",
        default=os.environ.get("AUTODASH_CHANNEL", can_config.DEFAULT_CHANNEL),
    )
    parser.add_argument(
        "--interface",
        default=os.environ.get("AUTODASH_INTERFACE", can_config.DEFAULT_INTERFACE),
        choices=("socketcan", "virtual"),
    )
    parser.add_argument(
        "--control-socket",
        default=os.environ.get("AUTODASH_CONTROL_SOCKET", str(CONTROL_SOCKET)),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return run(args.channel, args.interface, args.control_socket)


if __name__ == "__main__":
    raise SystemExit(main())
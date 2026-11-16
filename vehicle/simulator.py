from __future__ import annotations

import argparse
import os
import queue
import signal
import sys
import threading
import time
from pathlib import Path

from config import can_config
from config.settings import CONTROL_SOCKET, LOGS_DIR
from can_bus.can_logger import CanLogger
from can_bus.can_sender import CanSender
from can_bus.security_monitor import SecurityMonitor
from ecu.body_ecu import BodyECU
from ecu.engine_ecu import EngineECU
from ecu.gateway_ecu import GatewayECU
from ecu.transmission_ecu import TransmissionECU
from .control_server import ControlServer
from .vehicle_controller import VehicleController
from .vehicle_physics import VehiclePhysics
from .vehicle_state import VehicleState


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Vehicle simulation and ECU process")
    parser.add_argument(
        "--channel", default=os.environ.get("AUTODASH_CHANNEL", can_config.DEFAULT_CHANNEL)
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
    parser.add_argument("--log-dir", default=str(LOGS_DIR))
    parser.add_argument("--no-log", action="store_true")
    parser.add_argument("--duration", type=float, default=0.0)
    parser.add_argument("--verbose", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    log_dir = Path(args.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    security = SecurityMonitor(log_dir / "security.log")
    logger = None if args.no_log else CanLogger(log_dir / "can.log")
    sender: CanSender | None = None
    server: ControlServer | None = None

    try:
        sender = CanSender(args.channel, args.interface)
    except Exception as error:
        print(
            f"Unable to open CAN interface {args.channel} ({args.interface}): {error}",
            file=sys.stderr,
        )
        print("Set up vcan0 with tools/setup_vcan.sh or run ./run.sh.", file=sys.stderr)
        return 1

    gateway = GatewayECU(sender=sender, logger=logger, security=security)
    state = VehicleState()
    physics = VehiclePhysics()
    controller = VehicleController(state)
    ecus = (EngineECU(gateway), TransmissionECU(gateway), BodyECU(gateway))

    command_queue: queue.Queue[dict] = queue.Queue()
    stop_event = threading.Event()

    def handle_signal(signum: int, _frame: object) -> None:
        stop_event.set()

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    try:
        server = ControlServer(Path(args.control_socket), command_queue)
    except OSError as error:
        print(f"Unable to create control socket: {error}", file=sys.stderr)
        sender.close()
        if logger is not None:
            logger.close()
        return 1

    server_thread = threading.Thread(
        target=server.serve_forever, name="ControlServer", daemon=True
    )
    server_thread.start()

    print(
        f"Simulator online: channel={args.channel} interface={args.interface} "
        f"control={args.control_socket}",
        flush=True,
    )

    started = time.monotonic()
    last = started
    last_report = started
    try:
        while not stop_event.is_set():
            now = time.monotonic()
            dt = min(0.05, now - last)
            last = now

            while True:
                try:
                    command = command_queue.get_nowait()
                except queue.Empty:
                    break
                if command.get("cmd") == "shutdown":
                    stop_event.set()
                    break
                controller.apply(command, now)

            controller.decay(now)
            physics.step(state, dt)
            for ecu in ecus:
                ecu.poll(state, now)

            if args.duration > 0 and now - started >= args.duration:
                break

            if args.verbose and now - last_report >= 1.0:
                last_report = now
                print(
                    f"speed={state.speed_abs:6.1f} km/h rpm={state.rpm:6.0f} "
                    f"gear={state.gear_text:>2} mode={state.driving_mode:<10} "
                    f"tx={gateway.transmitted} rej={gateway.rejected}",
                    flush=True,
                )

            sleep = 0.02 - (time.monotonic() - now)
            if sleep > 0:
                time.sleep(sleep)
    finally:
        if server is not None:
            server.close()
        sender.close()
        if logger is not None:
            logger.close()
        print("Simulator stopped", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_SCALE_FACTOR", "1")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QTimer  # noqa: E402

from config.settings import CONTROL_SOCKET, SCREENSHOTS_DIR  # noqa: E402
from dashboard.app import create_application  # noqa: E402
from dashboard.main_window import MainWindow  # noqa: E402


def send_json(sock: socket.socket, payload: dict) -> None:
    try:
        sock.sendall(
            (json.dumps(payload, separators=(",", ":")) + "\n").encode("utf-8")
        )
    except OSError:
        pass


class ScreenshotSequence:
    def __init__(
        self,
        app,
        window: MainWindow,
        control: socket.socket,
        output: Path,
        simulator: subprocess.Popen | None,
    ) -> None:
        self.app = app
        self.window = window
        self.control = control
        self.output = output
        self.simulator = simulator
        self.start = time.monotonic()
        self.actions = [
            (0.8, self.start_drive),
            (3.2, lambda: send_json(self.control, {"cmd": "door_toggle", "value": "fr"})),
            (3.8, lambda: self.capture("01_cockpit")),
            (4.2, lambda: self.window._switch_screen(1)),
            (4.7, lambda: self.capture("02_vehicle")),
            (5.1, lambda: self.window._switch_screen(2)),
            (5.6, lambda: self.capture("03_navigation")),
            (6.0, lambda: self.window._switch_screen(3)),
            (6.5, lambda: self.capture("04_media")),
            (6.9, lambda: self.window._switch_screen(4)),
            (7.4, lambda: self.capture("05_energy")),
            (7.8, lambda: self.window._switch_screen(5)),
            (8.3, lambda: self.capture("06_service")),
            (8.7, self.brake),
            (9.0, lambda: self.window._switch_screen(6)),
            (9.5, lambda: self.capture("07_settings")),
            (9.9, self.show_monitor),
            (10.6, lambda: self.capture("08_can_monitor")),
            (11.0, self.finish),
        ]
        self.index = 0
        self.timer = QTimer()
        self.timer.setInterval(40)
        self.timer.timeout.connect(self.tick)
        self.timer.start()

    def start_drive(self) -> None:
        send_json(self.control, {"cmd": "engine_start"})
        send_json(self.control, {"cmd": "set_gear", "value": "D"})
        send_json(self.control, {"cmd": "mode_set", "value": "COMFORT"})
        send_json(self.control, {"cmd": "light_toggle", "value": "low_beam"})
        send_json(self.control, {"cmd": "input", "name": "throttle", "value": 1})

    def brake(self) -> None:
        send_json(self.control, {"cmd": "input", "name": "throttle", "value": 0})
        send_json(self.control, {"cmd": "input", "name": "brake", "value": 1})

    def show_monitor(self) -> None:
        self.window.show_monitor()

    def capture(self, name: str) -> None:
        path = self.output / f"{name}.png"
        pixmap = self.window.grab()
        saved = pixmap.save(str(path))
        print(f"{'saved' if saved else 'failed'}: {path}")

    def finish(self) -> None:
        self.timer.stop()
        try:
            send_json(self.control, {"cmd": "input", "name": "brake", "value": 0})
            send_json(self.control, {"cmd": "indicator", "value": "off"})
            self.control.close()
        except OSError:
            pass
        if self.simulator is not None:
            self.simulator.terminate()
            try:
                self.simulator.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.simulator.kill()
        self.window.close()
        self.app.quit()

    def tick(self) -> None:
        elapsed = time.monotonic() - self.start
        while self.index < len(self.actions) and elapsed >= self.actions[self.index][0]:
            self.actions[self.index][1]()
            self.index += 1


def wait_for_socket(path: Path, timeout: float = 5.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if path.exists():
            return True
        time.sleep(0.05)
    return False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render dashboard screenshots")
    parser.add_argument("--channel", default=os.environ.get("AUTODASH_CHANNEL", "vcan0"))
    parser.add_argument(
        "--interface", default=os.environ.get("AUTODASH_INTERFACE", "socketcan")
    )
    parser.add_argument("--output", default=str(SCREENSHOTS_DIR))
    parser.add_argument("--no-sim", action="store_true")
    parser.add_argument("--control-socket", default="")
    args = parser.parse_args(argv)

    if args.interface == "virtual":
        print(
            "python-can's virtual interface is in-process only and cannot connect "
            "the dashboard to a separate simulator process. Use vcan0."
        )
        return 2

    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    socket_path = Path(
        args.control_socket
        or (
            str(CONTROL_SOCKET)
            if args.no_sim
            else f"/tmp/autodash-screenshot-{os.getpid()}.sock"
        )
    )
    simulator: subprocess.Popen | None = None
    if not args.no_sim:
        try:
            socket_path.unlink()
        except FileNotFoundError:
            pass
        log_dir = ROOT / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / "screenshot_simulator.log"
        log_file = log_path.open("w")
        simulator = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "vehicle.simulator",
                "--channel",
                args.channel,
                "--interface",
                args.interface,
                "--control-socket",
                str(socket_path),
                "--no-log",
            ],
            cwd=ROOT,
            stdout=log_file,
            stderr=subprocess.STDOUT,
        )
        if not wait_for_socket(socket_path):
            print("simulator did not create its control socket")
            if simulator.poll() is not None:
                print(log_path.read_text())
            else:
                simulator.terminate()
                try:
                    simulator.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    simulator.kill()
            return 1

    control = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        control.connect(str(socket_path))
    except OSError as error:
        print(f"cannot connect to control socket: {error}")
        if simulator is not None:
            simulator.terminate()
        return 1

    app = create_application([])
    window = MainWindow(
        channel=args.channel,
        interface=args.interface,
        control_socket=socket_path,
    )
    window.resize(1600, 900)
    window.show()
    sequence = ScreenshotSequence(app, window, control, output, simulator)
    app._screenshot_sequence = sequence  # type: ignore[attr-defined]
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

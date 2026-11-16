# Testing and Verification

## Automated tests

```bash
.venv/bin/python -m pytest -q
```

Current result: **41 passed**.

Test coverage:

| File | Coverage |
| --- | --- |
| `tests/test_can_roundtrip.py` | Every CAN spec encodes/decodes; DLC and unknown-ID rejection |
| `tests/test_vehicle_simulation.py` | Ignition default/interlocks, gear/mode/light/body commands, moving-gear lockout, parking-brake hold, acceleration/upshift/fuel use, indicator blinking |
| `tests/test_dashboard_model.py` | Snapshot decoding from CAN, link state, door warning, low fuel/battery warnings, frame counts |
| `tests/test_control_and_ui.py` | Control JSON round-trip, offscreen cockpit render at 1600×780, engine-button state, hidden-monitor work suppression, 4K cockpit scaling, runtime path sanity |
| `tests/conftest.py` | Offscreen Qt platform and session `QApplication` fixture |

The Qt test does not need a display server:

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q
```

## CAN simulator checks

Virtual python-can bus, no kernel setup:

```bash
.venv/bin/python -m vehicle.simulator \
    --interface virtual --channel test \
    --duration 2 --no-log \
    --control-socket /tmp/autodash-test.sock --verbose
```

Expected: simulator prints `Simulator online`, several verbose status lines,
`Simulator stopped`, and exits 0.

SocketCAN check:

```bash
./tools/setup_vcan.sh
timeout 10 .venv/bin/python -m vehicle.simulator --verbose \
    --control-socket /tmp/autodash-test.sock &
candump -ta -x vcan0
```

Expected frames include `101`, `102`, `105`, `110`, `115`, and the other IDs.
`0x101` should appear at roughly 50 Hz (period 20 ms).

## Full-stack run

```bash
./tools/setup_vcan.sh
./run.sh
```

Expected:

- Simulator creates the control socket and starts publishing.
- Dashboard opens at 1600×900.
- Header shows `CAN LINK` and `VCAN0`.
- Press `E` to start the engine, then `G` (to D) and `W`/`↑` to drive.
- The centre console shows `ENGINE RUNNING` and the start button reads
  `STOP ENGINE`.
- Mode changes via `V` change the theme.
- `F12` opens a live frame terminal.
- Closing the dashboard stops the simulator started by `run.sh`.

Useful checks while running:

```bash
candump -ta -x vcan0
.venv/bin/python tools/control_cli.py ping
.venv/bin/python tools/control_cli.py --hold 2 input throttle 1
```

## Screenshot generation

```bash
.venv/bin/python tools/generate_screenshots.py
```

This starts its own simulator on `vcan0`, opens the dashboard with the Qt
offscreen platform, drives the car, switches screens, captures eight PNGs into
`screenshots/`, then exits. It requires `vcan0`; the in-process `virtual` backend
is rejected because the screenshot dashboard and simulator are separate
processes. It uses a dedicated control socket so it can run
alongside another simulator for short periods, though duplicate CAN traffic is
possible if another simulator is active on the same bus.

Outputs:

```text
screenshots/01_cockpit.png
screenshots/02_vehicle.png
screenshots/03_navigation.png
screenshots/04_media.png
screenshots/05_energy.png
screenshots/06_service.png
screenshots/07_settings.png
screenshots/08_can_monitor.png
```

Set `QT_QPA_PLATFORM=offscreen` manually if the script's default is overridden.
The script logs simulator startup to `logs/screenshot_simulator.log`.

To capture against an already-running simulator:

```bash
.venv/bin/python tools/generate_screenshots.py --no-sim \
    --control-socket /tmp/automotive-dashboard-$(id -u)/control.sock
```

## Control protocol smoke tests

```bash
.venv/bin/python tools/control_cli.py gear_cycle_mode
.venv/bin/python tools/control_cli.py set_gear D
.venv/bin/python tools/control_cli.py mode_set SPORT
.venv/bin/python tools/control_cli.py light_toggle low_beam
.venv/bin/python tools/control_cli.py door_toggle fr
.venv/bin/python tools/control_cli.py close_all
.venv/bin/python tools/control_cli.py parking_brake_toggle
.venv/bin/python tools/control_cli.py trip_reset
```

Held inputs are released on disconnect; use `--hold` for one-shot checks:

```bash
.venv/bin/python tools/control_cli.py --hold 3 input throttle 1
```

## Troubleshooting

### `vcan0 is not available`

```bash
sudo modprobe vcan
sudo ip link add dev vcan0 type vcan
sudo ip link set vcan0 up
ip -details link show vcan0
```

or run `./tools/setup_vcan.sh`.

### `Unable to open CAN interface`

- Check `ip link show vcan0`.
- Ensure the interface is up.
- Confirm `python-can` and SocketCAN support are installed.
- Run the offscreen UI test or `tools/generate_screenshots.py`; both exercise the
  real widget tree without needing a display.

### Dashboard shows `NO CAN LINK`

- Confirm the simulator is running.
- Confirm both processes use the same channel/interface.
- Check `candump vcan0` for traffic.
- Check the in-app monitor for invalid frames or unknown IDs.

### Control actions do nothing

- Confirm the control socket exists and is the same path used by both processes.
- Check `Settings → CAN diagnostics → Control socket`.
- Test with `tools/control_cli.py ping`.
- Remember held inputs are released if no heartbeat arrives for 2 seconds.
- A dashboard disconnect releases all inputs.

### External `candump` shows nothing

The python-can `virtual` interface is in-process only. Use SocketCAN
(`vcan0`) with `candump` or the in-app `F12` monitor for end-to-end runs.

### Qt offscreen warnings

Offscreen rendering can print platform plugin warnings. They are harmless if
the PNGs are produced and the command exits 0. The screenshot script keeps the
screenshot sequence object alive for the lifetime of the Qt event loop; without
that reference Qt may garbage-collect the timer and exit without images.

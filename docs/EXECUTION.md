# Execution

This document describes how to run the Automotive Dashboard Simulator.

## Prerequisites

- Linux
- Python 3.10+
- A virtual environment with dependencies installed:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

- System packages (Debian/Ubuntu):

```bash
sudo apt install python3-venv can-utils
```

## SocketCAN setup

End-to-end runs require the `vcan` kernel module and a `vcan0` interface:

```bash
sudo modprobe vcan
sudo ip link add dev vcan0 type vcan
sudo ip link set vcan0 up
ip -details link show vcan0
```

The helper scripts automate this:

```bash
./tools/setup_vcan.sh
```

To remove the interface when finished:

```bash
./tools/teardown_vcan.sh
```

## Full-stack run

Launch the simulator, dashboard, CAN monitor, and live CAN signal decoder:

```bash
./tools/setup_vcan.sh
./run.sh
```

`./run.sh`:

1. Checks that the virtual environment exists at `.venv/bin/python`.
2. Verifies `vcan0` exists and is up.
3. Starts `vehicle.simulator` in the background on `vcan0`.
4. Waits for the simulator control socket to appear.
5. Launches the CAN monitor (`tools/monitor_can.py`) in a terminal.
6. Launches the dashboard GUI (`main.py`).
7. Launches the live CAN signal decoder (`tools/live_can_decoder.py`) in a terminal.
8. Stops the simulator when the dashboard exits.

Press `E` to start the engine, then `G` (to `D`) and `W`/`↑` to drive. Press
`F12` to open the in-app CAN monitor. Closing the dashboard stops the simulator
started by `run.sh`.

## Running components separately

Simulator:

```bash
.venv/bin/python -m vehicle.simulator --verbose
```

Dashboard:

```bash
.venv/bin/python main.py
```

The dashboard and simulator must use the same channel/interface. Defaults are
`vcan0` / `socketcan`.

## Attaching to an already-running simulator

```bash
AUTODASH_EXTERNAL_SIM=1 \
AUTODASH_CONTROL_SOCKET=/tmp/automotive-dashboard-$(id -u)/control.sock \
./run.sh
```

## Configuration

Environment variables:

| Variable | Default | Purpose |
| --- | --- | --- |
| `AUTODASH_CHANNEL` | `vcan0` | CAN channel |
| `AUTODASH_INTERFACE` | `socketcan` | SocketCAN interface name |
| `AUTODASH_CONTROL_SOCKET` | `$XDG_RUNTIME_DIR/automotive-dashboard-<uid>/control.sock` | Unix control socket |
| `AUTODASH_EXTERNAL_SIM` | unset | Set to `1` to skip starting a simulator in `run.sh` |

Simulator options: `--channel`, `--interface`, `--control-socket`, `--log-dir`,
`--no-log`, `--duration`, `--verbose`.

## Logs

Runtime logs are written to `logs/`:

- `simulator.out` / `dashboard.out` — process output from `run.sh`.
- `can-*.log` — rotating CAN CSV log.
- `security.log` — security/event log.

Logs are excluded from version control (see `.gitignore`).

## Troubleshooting

### `vcan0 is not available`

```bash
sudo modprobe vcan
sudo ip link add dev vcan0 type vcan
sudo ip link set vcan0 up
```

or run `./tools/setup_vcan.sh`.

### `Unable to open CAN interface`

- Check `ip link show vcan0`.
- Ensure the interface is up.
- Confirm `python-can` and SocketCAN support are installed.

### Dashboard shows `NO CAN LINK`

- Confirm the simulator is running.
- Confirm both processes use the same channel/interface.
- Check `candump vcan0` for traffic.
- Check the in-app monitor for invalid frames or unknown IDs.

### Control actions do nothing

- Confirm the control socket exists and is the same path used by both processes.
- Test with `tools/control_cli.py ping`.
- Remember held inputs are released if no heartbeat arrives for 2 seconds.

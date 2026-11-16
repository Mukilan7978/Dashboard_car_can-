# Architecture

## Process model

The project deliberately separates simulation from presentation:

1. **Simulator** (`python -m vehicle.simulator`)
   - Owns all vehicle state and physical behaviour.
   - Owns the ECUs, gateway, CAN sender, CAN logger, security monitor, and
     control server.
   - Never imports PySide6 or any `dashboard.*` module.
2. **Dashboard** (`python main.py`)
   - Owns Qt widgets, rendering, themes, navigation, and the CAN monitor.
   - Owns a CAN receiver and its own model of received data.
   - Never imports `vehicle.*`. Commands are sent over a Unix socket.
3. **Optional external tools**
   - `candump`/`can-utils` for raw bus observation.
   - `tools/control_cli.py` for direct simulator controls.
   - `tools/generate_screenshots.py` for headless rendering.

Vehicle data crosses the boundary only as CAN frames. The control channel is
only for simulated driver inputs and body/settings actions; it is not a
backdoor for dashboard data.

## Simulator loop

The simulator runs at approximately 50 Hz, with a capped `dt` of 50 ms:

1. Drain the command queue and apply commands through `VehicleController`.
2. Decay stale held inputs if no heartbeat has arrived for 2 seconds.
3. Step `VehiclePhysics` on `VehicleState`.
4. Poll each ECU; each ECU transmits due messages through `GatewayECU`.
5. Repeat until SIGINT/SIGTERM or `--duration` elapses.

The gateway validates ownership, rate, signal presence, enum/range values, and
encoding. It then sends the frame, logs it, decodes it for logging, and reports
it to the security monitor.

### Vehicle physics

- Speed is expressed in km/h; drag is quadratic and scaled so the model tops
  out near 260 km/h.
- `D` uses automatic gear selection with up/down thresholds. `M` uses the
  manual gear index, controlled by `gear_next`/`gear_prev`.
- Acceleration is limited by throttle, drag, rolling resistance, brake, and
  emergency brake.
- RPM is derived from wheel speed, final drive, selected gear ratio, and
  throttle; it is clamped to idle/redline.
- Fuel consumption increases with engine load; remaining fuel is converted to
  percent using the 60 L tank capacity.
- Engine temperature approaches a load-dependent target; battery voltage
  approaches the charging target while running.
- Tyre pressure changes with tyre temperature, which follows ambient
  temperature and speed.
- Indicators blink at 2 Hz using a monotonic clock; hazard overrides individual
  indicators in the active outputs.

## ECUs and CAN

`BaseECU` is a scheduled publisher. Each ECU owns a set of CAN IDs and builds
signal dictionaries for them. `GatewayECU` checks that the publishing ECU owns
the ID, applies a 50% minimum period guard, validates all values, encodes the
frame, and sends it.

Message ownership:

| Source | CAN IDs |
| --- | --- |
| ENGINE | `0x101`, `0x102`, `0x103`, `0x104`, `0x109`, `0x10A`, `0x10E`, `0x111`, `0x112`, `0x115` |
| TRANSMISSION | `0x105`, `0x10D` |
| BCM | `0x106`, `0x107`, `0x108`, `0x10B`, `0x10C`, `0x10F`, `0x110`, `0x113`, `0x114`, `0x116`, `0x117` |

`ClusterECU` contains decoder-side receive/staleness helpers, but the primary
simulator path uses `GatewayECU` plus the dashboard's own CAN source.

`CanLogger` writes CSV rows with wall time, ID, source, name, DLC, raw bytes,
and decoded summary. It rotates by size. `SecurityMonitor` records unknown IDs,
rate anomalies, invalid frames, and gateway rejections to a JSON-lines security
log, with deduplication and rotation.

## Control channel

`ControlServer` is a threaded Unix stream server. Each connection reads
newline-delimited JSON objects and puts valid command dictionaries on a shared
queue. `ping` is answered in-band. When a client disconnects, the server queues
`release_all`, which clears throttle, brake, clutch, steering, horn, and
emergency brake. The socket is chmodded to `0600`.

`VehicleController` is the only command interpreter. Unknown commands are
ignored. Commands are intentionally small and validated in the controller.

The dashboard's `ControlClient` runs a background daemon thread, reconnects if
the socket disappears, and drops queued commands while disconnected. A 500 ms
heartbeat keeps held inputs alive; the simulator releases all held inputs if
the heartbeat is older than 2 seconds.

## Dashboard data path

1. `CanBusSource` runs a `QThread` and receives raw frames from python-can.
2. `decode_message()` uses the shared message catalogue to produce a
   `DecodedFrame` with raw, physical, and display values.
3. `VehicleModel.ingest()` stores decoded values by signal and tracks link
   age, frame count, invalid count, and receive rate.
4. `VehicleModel.snapshot()` produces an immutable `VehicleSnapshot` plus
   warnings. Link is considered down when no valid frame has arrived within
   `LINK_TIMEOUT_S` (2 s).
5. The main window updates the current screen on a 33 ms (~30 fps) tick.
   Header/footer and settings diagnostics are throttled, and widgets skip
   repainting when their displayed state is unchanged. The hidden CAN monitor
   stops its append timer.
6. The theme is selected from the snapshot's driving mode. A theme change
   applies a new stylesheet and tells custom-painted widgets to repaint.

The UI only refreshes the visible screen while the header, footer, and monitor
continue to update. Screens retain the last snapshot so switching screens
renders immediately.

## Rendering

- All icons, gauges, charts, maps, and vehicle diagrams are painted with
  `QPainter`.
- `ArcGauge` caches its static gauge background in a `QPixmap`, keyed by size,
  device pixel ratio, and theme.
- Gauges use animated values for speed and RPM to avoid jitter.
- The layout target is 1600×900; minimum window size is 1280×720.
- The media and navigation screens display explicit simulated-service
  disclaimers.

## Failure and safety behaviour

- No CAN frames for more than 2 seconds: dashboard marks the link offline,
  gauges dim, and screens show `NO CAN LINK` / `NO CAN DATA`.
- Unknown/invalid CAN IDs or DLC mismatches: counted as invalid, shown in the
  monitor and settings diagnostics, and recorded by the security monitor.
- Simulator cannot open CAN: prints a setup hint and exits non-zero.
- Engine OFF at startup: throttle is inhibited until `engine_start`/`E`.
- Parking brake applied: the vehicle is held stationary and throttle is
  inhibited until the brake is released.
- Control client disconnects: held inputs are released.
- Dashboard closes: its control client stops, which causes the server to
  release held inputs; `run.sh` also stops the simulator it started.
- Lost CAN link does not affect the simulator's control server; the dashboard
  remains usable for local UI exploration.

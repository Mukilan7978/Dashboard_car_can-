# Controls

## Keyboard

The dashboard installs a global Qt event filter. Driving keys remain active
after clicking buttons and sliders; only text-entry fields (`QLineEdit`,
`QTextEdit`, `QPlainTextEdit`) capture the keyboard. Screen, fullscreen, and
monitor shortcuts remain available everywhere.

| Key | Action |
| --- | --- |
| `F1` | Cockpit |
| `F2` | Vehicle |
| `F3` | Navigation |
| `F4` | Media |
| `F5` | Energy |
| `F6` | Service |
| `F7` | Settings |
| `Ctrl+1`…`Ctrl+7` | Same screen selection |
| `G` | Cycle gear: P → R → N → D → M; while moving the cycle is N → D → M |
| `M` | Manual gear up while in M |
| `N` | Manual gear down while in M |
| `V` | Cycle driving mode ECO → COMFORT → SPORT → SPORT PLUS |
| `B` | Toggle steering weight COMFORT ↔ SPORT |
| `W` / `↑` | Throttle on press, off on release |
| `S` / `↓` | Brake on press, off on release |
| `A` / `←` | Steer left while held |
| `D` / `→` | Steer right while held |
| `Left Shift` | Toggle left indicator on release |
| `Right Shift` | Toggle right indicator on release |
| `,` | Left indicator fallback |
| `.` | Right indicator fallback |
| `Space` | Emergency brake while held |
| `H` | Horn while held |
| `E` | Start or stop the engine |
| `K` | Parking brake toggle (holds the car and blocks acceleration) |
| `F11` | Toggle fullscreen |
| `F12` | Toggle CAN monitor |
| `Esc` | Close the monitor; leave fullscreen if active |

Shift handling:

- The physical Shift side is identified from `nativeScanCode` 50 (left) and
  62 (right), with virtual-key fallbacks and a single-held-side fallback.
- Shift press does not send anything. Shift release sends the indicator command
  only if Shift was not used as a modifier in the meantime.
- `,` and `.` are provided for environments where Shift side detection is
  unreliable.

## Mouse actions

### Vehicle screen (`F2`)

- Door buttons `FL`, `FR`, `RL`, `RR`: toggle each door.
- `CLOSE ALL`: close doors and clear body openings/mirrors.
- `LOW`, `HIGH`, `DRL`, `FOG`: toggle each lamp.
- `ALL LIGHTS OFF`: turn off low/high/DRL/fog.
- `BONNET`, `BOOT`: toggle openings.
- `HAZARD`: toggle hazard lamps.

### Settings screen (`F7`)

- Driving mode buttons: `ECO`, `COMFORT`, `SPORT`, `SPORT PLUS`.
- Steering weight buttons: `COMFORT`, `SPORT`.
- `ENGINE START/STOP`, `PARK BRAKE`, `SEATBELT`, `RESET TRIP`.

### Cockpit start/stop (`F1`)

- The centre console shows engine, gear, driving mode, link, and warning state.
- `START ENGINE` / `STOP ENGINE` is clickable and mirrors the `E` shortcut.
- Engine START/STOP and gear changes produce a fading toast notification.
- Lighting toggles, indicators, `ALL LIGHTS OFF`.
- Door buttons, bonnet/boot, mirror folding, `CLOSE ALL`.

### Media screen (`F4`)

- Play/pause, previous, next, playlist selection, volume slider. All media is
  simulated and produces no audio.

## Simulator control protocol

Transport: Unix domain stream socket, default
`$XDG_RUNTIME_DIR/automotive-dashboard-<uid>/control.sock`.

Protocol: one UTF-8 JSON object per line (`\n` terminated). Invalid JSON and
non-object JSON are ignored. Multiple clients are allowed. The socket is
created with mode `0600`.

### Commands

| Command | Fields | Effect |
| --- | --- | --- |
| `ping` | — | Server replies `{"ok":true}` on the same connection |
| `heartbeat` | — | Refreshes the held-input timeout |
| `input` | `name`, `value` | Set a held input |
| `release_all` | — | Clear throttle, brake, clutch, steering, horn, emergency brake |
| `engine_start` | — | Start the engine (idempotent) |
| `engine_stop` | — | Stop the engine and clear throttle (idempotent) |
| `engine_toggle` | — | Toggle engine on/off |
| `gear_next` | — | Next gear (or manual up in M) |
| `gear_prev` | — | Previous gear (or manual down in M) |
| `gear_cycle_mode` | — | Cycle P/R/N/D/M, or N/D/M while moving |
| `set_gear` | `value` | Set `P`, `R`, `N`, `D`, or `M` |
| `indicator` | `value` | `left`, `right`, or `off` |
| `hazard_toggle` | — | Toggle hazard |
| `light_toggle` | `value` | `low_beam`, `high_beam`, `drl`, `fog` |
| `all_lights_off` | — | Turn off all controllable lamps |
| `door_toggle` | `value` | `fl`, `fr`, `rl`, `rr` |
| `close_all` | — | Close doors, bonnet, boot, and mirrors |
| `bonnet_toggle` | — | Toggle bonnet |
| `boot_toggle` | — | Toggle boot |
| `mirror_toggle` | `value` | `l` or `r` |
| `mode_set` | `value` | `ECO`, `COMFORT`, `SPORT`, `SPORT PLUS` |
| `steering_setting` | `value` | `COMFORT` or `SPORT` |
| `parking_brake_toggle` | — | Toggle parking brake |
| `seatbelt_toggle` | — | Toggle seatbelt |
| `trip_reset` | — | Reset trip distance/time/fuel-used/efficiency |
| `shutdown` | — | Stop the simulator cleanly |

`input` names:

| Name | Value type | Notes |
| --- | --- | --- |
| `throttle` | bool/number | Non-zero means full throttle |
| `brake` | bool/number | Non-zero means full brake |
| `clutch` | bool/number | Non-zero means clutch pressed (100%) |
| `steering` | float | Clamped to -1.0…1.0 |
| `horn` | bool | Horn state |
| `emergency_brake` | bool | Emergency brake state |

### Held input lifetime

`throttle`, `brake`, `clutch`, `steering`, `horn`, and `emergency_brake` are
held states. The dashboard sends `heartbeat` every 500 ms while it is running.
If the simulator has seen a heartbeat and then none arrives for 2 seconds, all
held inputs are released.

A client disconnect also queues `release_all`. For a one-shot CLI command that
sets a held input, keep the socket open long enough for the effect:

```bash
.venv/bin/python tools/control_cli.py --hold 3 input throttle 1
```

Interactive mode keeps the connection open until `quit`/`exit`:

```bash
.venv/bin/python tools/control_cli.py
```

### Examples

```bash
# Select drive and sport mode
.venv/bin/python tools/control_cli.py --socket /tmp/control.sock \
    '{"cmd":"set_gear","value":"D"}'
.venv/bin/python tools/control_cli.py --socket /tmp/control.sock \
    '{"cmd":"mode_set","value":"SPORT"}'

# Turn on low beam
.venv/bin/python tools/control_cli.py light_toggle low_beam

# Open the front-right door
.venv/bin/python tools/control_cli.py door_toggle fr

# Hold throttle for 3 seconds
.venv/bin/python tools/control_cli.py --hold 3 input throttle 1

# Interactive JSON / shorthand
.venv/bin/python tools/control_cli.py
```

### Deterministic test flow

For screenshots or headless testing, connect a control client, send commands,
keep the connection open while the dashboard renders, then close it. The
provided `tools/generate_screenshots.py` does this and saves eight PNGs.

## Fault handling summary

- The engine starts OFF; throttle has no effect until it is started.
- With the parking brake applied the car is held stationary and throttle is
  inhibited.
- Moving faster than 5 km/h prevents selecting P or R.
- Selecting P forces speed to zero, manual gear 1, and parking brake on.
- The dashboard releases throttle, brake, steering, horn, and emergency brake
  when the window loses focus or closes.
- No heartbeat for 2 seconds releases all held inputs.
- Disconnecting any control client queues `release_all`.
- Dashboard CAN link loss does not stop command delivery; body/settings actions
  can still be sent if the control socket is available.

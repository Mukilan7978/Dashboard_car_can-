# CAN Message Catalogue

## Bus conventions

- Standard 11-bit CAN identifiers.
- Little-endian (`struct` format prefix `<`).
- Single-frame messages; DLC must equal the specification.
- Default bitrate for SocketCAN setup: 500 kbit/s.
- `Period` is the normal publishing interval.
- `Timeout` is the freshness limit used for link/staleness checks.
- Bit signals pack into the listed byte, bit 0 = least significant bit.
- Enum values are transmitted as unsigned bytes and decoded to labels by the
  dashboard model.

## Summary

| ID | Name | Source | DLC | Period | Timeout |
| --- | --- | --- | --- | --- | --- |
| `0x101` | Vehicle speed | ENGINE | 2 | 20 ms | 500 ms |
| `0x102` | Engine RPM | ENGINE | 2 | 20 ms | 500 ms |
| `0x103` | Engine temperature | ENGINE | 2 | 1000 ms | 3000 ms |
| `0x104` | Fuel level | ENGINE | 2 | 1000 ms | 3000 ms |
| `0x105` | Gear position | TRANSMISSION | 2 | 50 ms | 1000 ms |
| `0x106` | Turn indicators | BCM | 1 | 100 ms | 1000 ms |
| `0x107` | Headlights | BCM | 1 | 200 ms | 2000 ms |
| `0x108` | Brake status | BCM | 1 | 50 ms | 1000 ms |
| `0x109` | Engine status | ENGINE | 1 | 100 ms | 2000 ms |
| `0x10A` | Battery voltage | ENGINE | 2 | 1000 ms | 3000 ms |
| `0x10B` | Tyre pressure | BCM | 8 | 1000 ms | 3000 ms |
| `0x10C` | Body status | BCM | 1 | 200 ms | 2000 ms |
| `0x10D` | Clutch status | TRANSMISSION | 1 | 50 ms | 1000 ms |
| `0x10E` | Driving mode | ENGINE | 1 | 1000 ms | 3000 ms |
| `0x10F` | Ambient temperature | BCM | 2 | 1000 ms | 5000 ms |
| `0x110` | Steering angle | BCM | 2 | 20 ms | 500 ms |
| `0x111` | Odometer and trip | ENGINE | 8 | 1000 ms | 3000 ms |
| `0x112` | Driving information | ENGINE | 8 | 1000 ms | 3000 ms |
| `0x113` | Horn | BCM | 1 | 100 ms | 1000 ms |
| `0x114` | Tyre temperature | BCM | 4 | 1000 ms | 3000 ms |
| `0x115` | Engine load | ENGINE | 1 | 50 ms | 1000 ms |
| `0x116` | Steering setting | BCM | 1 | 1000 ms | 3000 ms |
| `0x117` | Cabin status | BCM | 1 | 1000 ms | 3000 ms |

## Signal layouts

### `0x101` Vehicle speed — ENGINE

| Signal | Byte | Format | Scale | Offset | Unit | Range |
| --- | --- | --- | --- | --- | --- | --- |
| `speed` | 0 | `H` (u16) | 0.01 | 0 | km/h | 0–260 |

### `0x102` Engine RPM — ENGINE

| Signal | Byte | Format | Scale | Offset | Unit | Range |
| --- | --- | --- | --- | --- | --- | --- |
| `rpm` | 0 | `H` (u16) | 1 | 0 | rpm | 0–8000 |

### `0x103` Engine temperature — ENGINE

| Signal | Byte | Format | Scale | Offset | Unit | Range |
| --- | --- | --- | --- | --- | --- | --- |
| `engine_temp` | 0 | `h` (i16) | 0.1 | 0 | °C | -40–150 |

### `0x104` Fuel level — ENGINE

| Signal | Byte | Format | Scale | Offset | Unit | Range |
| --- | --- | --- | --- | --- | --- | --- |
| `fuel_level` | 0 | `H` (u16) | 0.1 | 0 | % | 0–100 |

### `0x105` Gear position — TRANSMISSION

| Signal | Byte | Format | Scale | Offset | Unit | Range |
| --- | --- | --- | --- | --- | --- | --- |
| `gear` | 0 | `B` (u8) | 1 | 0 | enum | see below |
| `manual_gear` | 1 | `B` (u8) | 1 | 0 | gear | 1–8 |

Gear enum: `0=P`, `1=R`, `2=N`, `3=D`, `4=M`.

### `0x106` Turn indicators — BCM

| Signal | Byte | Bit | Meaning |
| --- | --- | --- | --- |
| `left_indicator` | 0 | 0 | Left indicator active phase |
| `right_indicator` | 0 | 1 | Right indicator active phase |
| `hazard` | 0 | 2 | Hazard enabled |

Bits 3–7 unused.

### `0x107` Headlights — BCM

| Signal | Byte | Bit | Meaning |
| --- | --- | --- | --- |
| `low_beam` | 0 | 0 | Low beam |
| `high_beam` | 0 | 1 | High beam |
| `drl` | 0 | 2 | Daytime running lamps |
| `fog` | 0 | 3 | Fog lamps |
| `reverse_light` | 0 | 4 | Reverse lamp |

Bits 5–7 unused.

### `0x108` Brake status — BCM

| Signal | Byte | Bit | Meaning |
| --- | --- | --- | --- |
| `brake_pressed` | 0 | 0 | Brake pedal or emergency brake |
| `brake_light` | 0 | 1 | Brake light illuminated |

### `0x109` Engine status — ENGINE

| Signal | Byte | Bit | Meaning |
| --- | --- | --- | --- |
| `engine_running` | 0 | 0 | Engine running |
| `check_engine` | 0 | 1 | Check-engine fault |
| `oil_pressure` | 0 | 2 | Oil-pressure warning |
| `coolant_warning` | 0 | 3 | Coolant/overheat warning |

### `0x10A` Battery voltage — ENGINE

| Signal | Byte | Format | Scale | Offset | Unit | Range |
| --- | --- | --- | --- | --- | --- | --- |
| `battery_voltage` | 0 | `H` (u16) | 0.001 | 0 | V | 8–16 |

### `0x10B` Tyre pressure — BCM

| Signal | Byte | Format | Scale | Offset | Unit | Range |
| --- | --- | --- | --- | --- | --- | --- |
| `tyre_fl` | 0 | `H` (u16) | 0.001 | 0 | bar | 0–5 |
| `tyre_fr` | 2 | `H` (u16) | 0.001 | 0 | bar | 0–5 |
| `tyre_rl` | 4 | `H` (u16) | 0.001 | 0 | bar | 0–5 |
| `tyre_rr` | 6 | `H` (u16) | 0.001 | 0 | bar | 0–5 |

### `0x10C` Body status — BCM

| Signal | Byte | Bit | Meaning |
| --- | --- | --- | --- |
| `door_fl` | 0 | 0 | Front-left door open |
| `door_fr` | 0 | 1 | Front-right door open |
| `door_rl` | 0 | 2 | Rear-left door open |
| `door_rr` | 0 | 3 | Rear-right door open |
| `bonnet` | 0 | 4 | Bonnet open |
| `boot` | 0 | 5 | Boot open |
| `mirror_l` | 0 | 6 | Left mirror folded |
| `mirror_r` | 0 | 7 | Right mirror folded |

### `0x10D` Clutch status — TRANSMISSION

| Signal | Byte | Format | Scale | Offset | Unit | Range |
| --- | --- | --- | --- | --- | --- | --- |
| `clutch` | 0 | `B` (u8) | 1 | 0 | % | 0–100 |

### `0x10E` Driving mode — ENGINE

| Signal | Byte | Format | Scale | Offset | Unit | Range |
| --- | --- | --- | --- | --- | --- | --- |
| `driving_mode` | 0 | `B` (u8) | 1 | 0 | enum | see below |

Mode enum: `0=ECO`, `1=COMFORT`, `2=SPORT`, `3=SPORT PLUS`.

### `0x10F` Ambient temperature — BCM

| Signal | Byte | Format | Scale | Offset | Unit | Range |
| --- | --- | --- | --- | --- | --- | --- |
| `ambient_temp` | 0 | `h` (i16) | 0.1 | 0 | °C | -40–60 |

### `0x110` Steering angle — BCM

| Signal | Byte | Format | Scale | Offset | Unit | Range |
| --- | --- | --- | --- | --- | --- | --- |
| `steering_angle` | 0 | `h` (i16) | 0.1 | 0 | ° | -540–540 |

### `0x111` Odometer and trip — ENGINE

| Signal | Byte | Format | Scale | Offset | Unit | Range |
| --- | --- | --- | --- | --- | --- | --- |
| `odometer` | 0 | `I` (u32) | 0.1 | 0 | km | 0–999999 |
| `trip_distance` | 4 | `I` (u32) | 0.1 | 0 | km | 0–9999 |

### `0x112` Driving information — ENGINE

| Signal | Byte | Format | Scale | Offset | Unit | Range |
| --- | --- | --- | --- | --- | --- | --- |
| `avg_speed` | 0 | `H` (u16) | 0.1 | 0 | km/h | 0–260 |
| `instant_consumption` | 2 | `H` (u16) | 0.01 | 0 | L/100km | 0–99 |
| `avg_consumption` | 4 | `H` (u16) | 0.01 | 0 | L/100km | 0–99 |
| `trip_duration` | 6 | `H` (u16) | 1 | 0 | s | 0–65535 |

### `0x113` Horn — BCM

| Signal | Byte | Bit | Meaning |
| --- | --- | --- | --- |
| `horn` | 0 | 0 | Horn active |

### `0x114` Tyre temperature — BCM

| Signal | Byte | Format | Scale | Offset | Unit | Range |
| --- | --- | --- | --- | --- | --- | --- |
| `tyre_temp_fl` | 0 | `b` (i8) | 1 | -40 | °C | -40–85 |
| `tyre_temp_fr` | 1 | `b` (i8) | 1 | -40 | °C | -40–85 |
| `tyre_temp_rl` | 2 | `b` (i8) | 1 | -40 | °C | -40–85 |
| `tyre_temp_rr` | 3 | `b` (i8) | 1 | -40 | °C | -40–85 |

### `0x115` Engine load — ENGINE

| Signal | Byte | Format | Scale | Offset | Unit | Range |
| --- | --- | --- | --- | --- | --- | --- |
| `engine_load` | 0 | `B` (u8) | 1 | 0 | % | 0–100 |

### `0x116` Steering setting — BCM

| Signal | Byte | Format | Scale | Offset | Unit | Range |
| --- | --- | --- | --- | --- | --- | --- |
| `steering_setting` | 0 | `B` (u8) | 1 | 0 | enum | see below |

Steering enum: `0=COMFORT`, `1=SPORT`.

### `0x117` Cabin status — BCM

| Signal | Byte | Bit | Meaning |
| --- | --- | --- | --- |
| `seatbelt` | 0 | 0 | Seatbelt fastened |
| `parking_brake` | 0 | 1 | Parking brake engaged |

## Validation behaviour

- Wrong DLC: rejected by gateway/dashboard decoder.
- Unknown ID: rejected by gateway validation and shown as invalid by the
  dashboard.
- Enum values outside the catalogue: rejected by the gateway and marked invalid
  by the decoder.
- Numeric values outside range: rejected before encoding; decoded values
  outside range are marked invalid.
- Gateway rejects a message if the source does not own the ID, a required
  signal is missing, or the message arrives faster than half its nominal period.
- The dashboard waits up to 2 seconds without any valid frame before declaring
  `NO CAN LINK`.

#!/usr/bin/env python3
"""Live CAN monitor using python-can and SocketCAN.

Reads actual frames from the virtual CAN bus (vcan0) and prints:
  - Timestamp
  - CAN ID (hex)
  - DLC
  - Raw data bytes (hex)
  - Decoded signal names/values where known

Uses the same virtual CAN interface as the dashboard.
"""
import os
import sys
import time

# Ensure the project root is on the Python path so that `can_bus` is importable.
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import can
from can_bus.message_ids import CanId

# ---------------------------------------------------------------------------
# Helper: human‑readable line for a received CAN frame
# ---------------------------------------------------------------------------
def decode_frame(msg):
    """Return a human readable line for the frame."""
    ts = time.strftime("%H:%M:%S", time.localtime(msg.timestamp))
    sid = f"0x{msg.arbitration_id:X}"
    dlc = msg.dlc
    data_hex = " ".join(f"{b:02X}" for b in msg.data)

    # Manual decode for ENGINE_LOAD (0x115) – throttle percentage.
    # The message spec defines one unsigned byte (fmt 'B'), scale=1.0, min=0, max=100.
    if msg.arbitration_id == CanId.ENGINE_LOAD and msg.dlc >= 1:
        raw = msg.data[0]          # throttle * 100, 0‑100
        throttle_pct = raw         # already 0‑100 because engine_ecu multiplies by 100
        decoded_str = f"Throttle %={raw}"
    else:
        # Try the generic decoder (optional – may be absent)
        try:
            from can_bus.message_decoder import decode_message  # optional; if missing, fall back
            decoded = decode_message(msg.arbitration_id, msg.data)
            parts = []
            for name, value in decoded.items():
                parts.append(f"{name}={value}")
            # Rename engine_load to Throttle % for readability
            parts = [p.replace("engine_load=", "Throttle %=", 1) if p.startswith("engine_load=") else p for p in parts]
            decoded_str = "  ".join(parts) if parts else ""
        except Exception:           # pragma: no cover  – decoder may be missing
            decoded_str = ""

    if decoded_str:
        return f"{ts}   {sid}      {dlc}    {data_hex}  {decoded_str}"
    else:
        # fallback: just show raw data
        return f"{ts}   {sid}      {dlc}    {data_hex}"


# ---------------------------------------------------------------------------
# Main monitor loop
# ---------------------------------------------------------------------------
def main():
    channel = os.getenv("AUTODASH_CHANNEL", "vcan0")
    interface = os.getenv("AUTODASH_INTERFACE", "socketcan")

    try:
        bus = can.Bus(channel=channel, interface=interface)
    except Exception as e:
        print(f"Cannot connect to CAN bus channel={channel} interface={interface}: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Listening on {channel} ({interface}) – press Ctrl‑C to stop")
    try:
        while True:
            msg = bus.recv()
            if msg is None:
                continue
            line = decode_frame(msg)
            if line:
                print(line)
            else:
                # fallback raw print (should rarely happen)
                print(f"{ts}   0x{msg.arbitration_id:X}      {msg.dlc}    {' '.join(f'{b:02X}' for b in msg.data)}")
            sys.stdout.flush()
    except KeyboardInterrupt:
        pass
    finally:
        bus.shutdown()


if __name__ == "__main__":
    main()
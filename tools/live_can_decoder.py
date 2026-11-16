#!/usr/bin/env python3
"""Live CAN signal decoder - fourth terminal.

Independently receives actual frames from vcan0 and displays
detailed signal information ONLY when signals are active (non-zero
or True). Stays silent until you press pedals, turn indicators, etc.
"""
import can
import time
import sys

from can_bus.message_definitions import BY_ID, SPECS, SignalSpec, MessageSpec
from can_bus.can_decoder import decode_message


def get_signal_info(msg: can.Message, spec: MessageSpec | None = None) -> dict | None:
    """Extract signal details from a CAN frame using decode_message."""
    decoded = decode_message(msg)
    if not decoded.valid or decoded.spec is None:
        return None

    spec = decoded.spec if spec is None else spec
    info = {
        'timestamp': f"{time.time():.1f}",
        'can_id': f"0x{msg.arbitration_id:03X}",
        'message_name': spec.name,
        'dlc': spec.dlc,
        'data': msg.data.hex(),
        'valid': True,
        'spec': spec,
    }

    for signal in spec.signals:
        if signal.is_bit:
            val = decoded.values.get(signal.name, False)
            info[f'{signal.name}_bit'] = str(val)
            info[f'{signal.name}_raw'] = str(decoded.raw.get(signal.name, 0))
        else:
            raw_val = decoded.raw.get(signal.name, 0)
            physical = raw_val * signal.scale + signal.offset
            info[f'{signal.name}_raw'] = str(raw_val)
            info[f'{signal.name}_physical'] = f"{physical:.2f}"
            info[f'{signal.name}_unit'] = signal.unit or ''
            info[f'{signal.name}_min'] = str(signal.min_value) if signal.min_value is not None else 'N/A'
            info[f'{signal.name}_max'] = str(signal.max_value) if signal.max_value is not None else 'N/A'

    return info


def format_signal_detail(signal: SignalSpec) -> str:
    """Format a single signal's details for display."""
    lines = [
        f"  Signal Name: {signal.name}",
    ]
    if signal.is_bit:
        lines.append(f"  Start Bit: {signal.bit}")
        lines.append(f"  Length: 1 bit")
    else:
        lines.append(f"  Start Bit: (implicit, byte {signal.byte})")
        lines.append(f"  Length: 16 bits (typically)")
    lines.append(f"  Byte Order: Motorola/Big Endian")
    lines.append(f"  Signed: {'Signed' if signal.fmt in ('h', 'i') else 'Unsigned'}")
    lines.append(f"  Scale: {signal.scale}")
    lines.append(f"  Offset: {signal.offset}")
    lines.append(f"  Unit: {signal.unit or '—'}")
    if signal.min_value is not None:
        lines.append(f"  Minimum: {signal.min_value}")
    if signal.max_value is not None:
        lines.append(f"  Maximum: {signal.max_value}")
    if signal.enum is not None:
        lines.append(f"  Enumeration: {dict(signal.enum)}")
    return '\n'.join(lines)


def signal_is_active(signal: SignalSpec, frame_info: dict) -> bool:
    """Return True if the signal has a non-zero/active value."""
    if signal.is_bit:
        return frame_info.get(f'{signal.name}_bit', 'False') == 'True'
    try:
        val = float(frame_info.get(f'{signal.name}_physical', 0))
        return abs(val) > 0.05
    except (ValueError, TypeError):
        return False


def main():
    channel = 'vcan0'
    interface = 'socketcan'

    try:
        bus = can.Bus(channel=channel, interface=interface)
    except Exception as e:
        print(f"Cannot connect to CAN bus: {e}")
        sys.exit(1)

    print(f"Live CAN Signal Decoder on {channel} ({interface})")
    print("=" * 60)
    print("Waiting for active signals... (press pedals, indicators, etc.)")
    print("Stays silent until a signal becomes active.")
    print()

    try:
        while True:
            msg = bus.recv()
            if msg is None:
                continue

            frame_info = get_signal_info(msg)

            if frame_info:
                spec = frame_info.get('spec')
                if spec:
                    # Collect only active signals
                    active_signals = []
                    for signal in spec.signals:
                        if signal_is_active(signal, frame_info):
                            active_signals.append(signal)

                    # Only print if there's at least one active signal
                    if active_signals:
                        print(f"\nCAN ID:    {frame_info['can_id']}")
                        print(f"Message:   {frame_info['message_name']}")
                        print(f"DLC:       {frame_info['dlc']}")
                        print(f"Data:      {frame_info['data']}")
                        print(f"Timestamp: {frame_info['timestamp']}")
                        print()

                        for signal in active_signals:
                            print(format_signal_detail(signal))
                            print()
                            if signal.name in frame_info:
                                physical_val = frame_info.get(f'{signal.name}_physical', 'N/A')
                                raw_val = frame_info[f'{signal.name}_raw']
                                if not signal.is_bit:
                                    try:
                                        pval = float(physical_val)
                                        if abs(pval) < 0.05:
                                            physical_disp = "0.00"
                                        else:
                                            physical_disp = f"{pval:.2f}"
                                    except (ValueError, TypeError):
                                        physical_disp = physical_val
                                    print(f"  {signal.name}:")
                                    print(f"    Raw:      {raw_val}")
                                    print(f"    Physical: {physical_disp} {frame_info[f'{signal.name}_unit']}")
                                else:
                                    print(f"  {signal.name}:")
                                    print(f"    Raw:      {raw_val}")
                                    print(f"    Physical: {frame_info.get(f'{signal.name}_bit', 'False')}")
                        print("-" * 40)
            else:
                # Unknown CAN ID - show raw frame only if data is non-empty
                if any(b != 0 for b in msg.data):
                    print(f"\nCAN ID: 0x{msg.arbitration_id:03X} | DLC: {msg.dlc}")
                    print(f"Data:    {msg.data.hex()}")
                    print(f"Timestamp: {time.time():.1f}")
                    print(f"Note: ID not in project DBC database")
                    print("-" * 40)

            time.sleep(0.01)

    except KeyboardInterrupt:
        print("\nDecoder stopped by user")
    finally:
        bus.shutdown()


if __name__ == '__main__':
    main()
#!/usr/bin/env bash
set -euo pipefail

CHANNEL="${1:-vcan0}"

if ip link show "$CHANNEL" >/dev/null 2>&1; then
    sudo ip link set "$CHANNEL" down
    sudo ip link delete "$CHANNEL" type vcan
    echo "Removed $CHANNEL"
else
    echo "$CHANNEL does not exist"
fi

#!/usr/bin/env bash
set -euo pipefail

CHANNEL="${1:-vcan0}"

if ip link show "$CHANNEL" >/dev/null 2>&1; then
    echo "$CHANNEL already exists; setting it up."
else
    sudo modprobe vcan
    sudo ip link add dev "$CHANNEL" type vcan
fi

sudo ip link set "$CHANNEL" up
ip -details link show "$CHANNEL"

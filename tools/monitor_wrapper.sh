#!/usr/bin/env bash
set -euo pipefail

CHANNEL="${1:-vcan0}"

if ! command -v candump >/dev/null 2>&1; then
    echo "candump is not installed. Install can-utils to use the external monitor."
    exit 1
fi

exec candump -ta -x "$CHANNEL"

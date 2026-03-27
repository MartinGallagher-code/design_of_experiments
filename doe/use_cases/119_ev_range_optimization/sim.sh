#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: EV Range Optimization
set -euo pipefail

OUTFILE=""
SP=""
CT=""
RL=""
TT=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --speed_kph) SP="$2"; shift 2 ;;
        --cabin_temp) CT="$2"; shift 2 ;;
        --regen_level) RL="$2"; shift 2 ;;
        --tire_type) TT="$2"; shift 2 ;;
        --battery_kwh) shift 2 ;;
        --vehicle_type) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$SP" ] || [ -z "$CT" ] || [ -z "$RL" ] || [ -z "$TT" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v SP="$SP" -v CT="$CT" -v RL="$RL" -v TT="$TT" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    sp = (SP - 90) / 30;
    ct = (CT - 22) / 4;
    rl = (RL - 2) / 1;
    tt = (TT == "low_rolling") ? 1 : -1;
    kwh = 18 + 4*sp + 1.5*ct - 1.2*rl - 1.5*tt + 1.5*sp*sp + 0.5*ct*ct + 0.3*sp*ct;
    range_ = 75 / kwh * 100;
    if (kwh < 10) kwh = 10;
    if (range_ < 150) range_ = 150;
    printf "{\"range_km\": %.0f, \"kwh_per_100km\": %.1f}", range_ + n1*8, kwh + n2*0.5;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

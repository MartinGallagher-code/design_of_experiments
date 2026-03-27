#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Drum Head Tuning
set -euo pipefail

OUTFILE=""
BT=""
RT=""
MF=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --batter_torque) BT="$2"; shift 2 ;;
        --reso_torque) RT="$2"; shift 2 ;;
        --muffle_pct) MF="$2"; shift 2 ;;
        --drum_size) shift 2 ;;
        --head_type) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$BT" ] || [ -z "$RT" ] || [ -z "$MF" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v BT="$BT" -v RT="$RT" -v MF="$MF" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    bt = (BT - 50) / 30;
    rt = (RT - 50) / 30;
    mf = (MF - 25) / 25;
    res = 6.0 + 0.5*bt + 0.8*rt - 1.5*mf - 0.4*bt*bt - 0.3*rt*rt + 0.3*bt*rt;
    over = 5.0 - 0.3*bt - 0.2*rt + 2.0*mf + 0.2*bt*bt - 0.3*mf*mf + 0.2*bt*mf;
    if (res < 1) res = 1; if (res > 10) res = 10;
    if (over < 1) over = 1; if (over > 10) over = 10;
    printf "{\"resonance\": %.1f, \"overtone_control\": %.1f}", res + n1*0.3, over + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

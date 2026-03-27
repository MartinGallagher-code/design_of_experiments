#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Natural Fabric Dyeing
set -euo pipefail

OUTFILE=""
DC=""
BT=""
IM=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --dye_concentration_pct) DC="$2"; shift 2 ;;
        --bath_temp_c) BT="$2"; shift 2 ;;
        --immersion_min) IM="$2"; shift 2 ;;
        --fabric) shift 2 ;;
        --mordant) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$DC" ] || [ -z "$BT" ] || [ -z "$IM" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v DC="$DC" -v BT="$BT" -v IM="$IM" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    dc = (DC - 17.5) / 12.5; bt = (BT - 67.5) / 27.5; im = (IM - 75) / 45;
    depth = 3.0 + 1.5*dc + 0.8*bt + 0.5*im - 0.4*dc*dc - 0.3*bt*bt + 0.2*dc*bt;
    fast = 3.5 + 0.3*dc + 0.5*bt + 0.3*im - 0.2*dc*dc + 0.1*bt*bt - 0.15*im*im + 0.1*bt*im;
    if (depth < 0.5) depth = 0.5;
    if (fast < 1) fast = 1; if (fast > 5) fast = 5;
    printf "{\"color_depth\": %.1f, \"wash_fastness\": %.1f}", depth + n1*0.2, fast + n2*0.15;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

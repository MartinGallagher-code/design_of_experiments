#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Injection Molding Quality (4-response multi-objective)
set -euo pipefail

OUTFILE=""
MT=""
IP=""
CT=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --melt_temp) MT="$2"; shift 2 ;;
        --injection_pressure) IP="$2"; shift 2 ;;
        --cooling_time) CT="$2"; shift 2 ;;
        --mold_material) shift 2 ;;
        --part_weight) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$MT" ] || [ -z "$IP" ] || [ -z "$CT" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v MT="$MT" -v IP="$IP" -v CT="$CT" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;
    n3 = (rand() - 0.5) * 2;
    n4 = (rand() - 0.5) * 2;

    # Normalize factors to [-1, 1]
    mt = (MT - 240) / 40;
    ip = (IP - 85) / 35;
    ct = (CT - 20) / 10;

    # Surface finish: higher is better, peaks at mid-high temp and pressure
    sf = 1.5 + 0.3*mt + 0.2*ip + 0.1*ct - 0.15*mt*mt - 0.1*ip*ip + 0.05*mt*ip;
    sf = sf + n1 * 0.05;
    if (sf < 0.1) sf = 0.1;
    if (sf > 2.0) sf = 2.0;

    # Dimensional accuracy: best at moderate temp, high pressure, long cooling
    da = 98.0 + 0.5*ip + 0.8*ct - 0.6*mt*mt - 0.3*ip*ip + 0.2*mt*ct;
    da = da + n2 * 0.3;
    if (da < 95) da = 95;
    if (da > 100) da = 100;

    # Cycle time: increases with cooling time, decreases with temp
    cyc = 35 - 5*mt + 2*ip + 10*ct + 1.5*mt*ct;
    cyc = cyc + n3 * 1.5;
    if (cyc < 15) cyc = 15;
    if (cyc > 60) cyc = 60;

    # Warpage: worse at high temp, better with long cooling
    warp = 0.7 + 0.3*mt - 0.1*ip - 0.25*ct + 0.1*mt*mt + 0.05*mt*ip;
    warp = warp + n4 * 0.04;
    if (warp < 0) warp = 0;
    if (warp > 1.5) warp = 1.5;

    printf "{\"surface_finish\": %.3f, \"dimensional_accuracy\": %.2f, \"cycle_time\": %.1f, \"warpage\": %.3f}", sf, da, cyc, warp;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

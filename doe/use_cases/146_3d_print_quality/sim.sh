#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: 3D Print Quality Tuning
set -euo pipefail

OUTFILE=""
LH=""
PS=""
NT=""
IP=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --layer_height_mm) LH="$2"; shift 2 ;;
        --print_speed) PS="$2"; shift 2 ;;
        --nozzle_temp_c) NT="$2"; shift 2 ;;
        --infill_pct) IP="$2"; shift 2 ;;
        --material) shift 2 ;;
        --bed_temp) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$LH" ] || [ -z "$PS" ] || [ -z "$NT" ] || [ -z "$IP" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v LH="$LH" -v PS="$PS" -v NT="$NT" -v IP="$IP" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    lh = (LH - 0.2) / 0.1;
    ps = (PS - 55) / 25;
    nt = (NT - 205) / 15;
    ip = (IP - 30) / 20;
    surf = 7.0 - 1.5*lh - 0.8*ps + 0.5*nt - 0.2*ip - 0.3*lh*lh + 0.2*ps*ps - 0.4*nt*nt + 0.3*lh*ps;
    time_ = 60 - 15*lh - 12*ps + 0.5*nt + 8*ip + 3*lh*lh + 2*ps*ps + 1.5*lh*ip;
    if (surf < 1) surf = 1; if (surf > 10) surf = 10;
    if (time_ < 15) time_ = 15;
    printf "{\"surface_quality\": %.1f, \"print_time_min\": %.0f}", surf + n1*0.3, time_ + n2*3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

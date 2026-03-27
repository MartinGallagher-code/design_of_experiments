#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Drone Aerial Photography
set -euo pipefail

OUTFILE=""
AL=""
GA=""
FS=""
OP=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --altitude_m) AL="$2"; shift 2 ;;
        --gimbal_angle) GA="$2"; shift 2 ;;
        --flight_speed) FS="$2"; shift 2 ;;
        --overlap_pct) OP="$2"; shift 2 ;;
        --camera) shift 2 ;;
        --wind) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$AL" ] || [ -z "$GA" ] || [ -z "$FS" ] || [ -z "$OP" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v AL="$AL" -v GA="$GA" -v FS="$FS" -v OP="$OP" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    al = (AL - 75) / 45;
    ga = (GA - -67.5) / 22.5;
    fs = (FS - 7) / 5;
    op = (OP - 72.5) / 12.5;
    gsd = 2.5 + 1.5*al + 0.3*ga + 0.1*fs - 0.2*op;
    blur = 3.0 + 0.3*al - 0.5*ga + 1.5*fs - 0.2*op + 0.3*fs*fs + 0.2*al*fs;
    if (gsd < 0.5) gsd = 0.5;
    if (blur < 1) blur = 1; if (blur > 10) blur = 10;
    printf "{\"gsd_cm\": %.1f, \"blur_score\": %.1f}", gsd + n1*0.2, blur + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Meal Timing and Energy Levels
set -euo pipefail

OUTFILE=""
MP=""
EW=""
PP=""
MC=""
FB=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --meals_per_day) MP="$2"; shift 2 ;;
        --eating_window_hrs) EW="$2"; shift 2 ;;
        --protein_pct) PP="$2"; shift 2 ;;
        --morning_cal_pct) MC="$2"; shift 2 ;;
        --fiber_g) FB="$2"; shift 2 ;;
        --total_calories) shift 2 ;;
        --activity_level) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$MP" ] || [ -z "$EW" ] || [ -z "$PP" ] || [ -z "$MC" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v MP="$MP" -v EW="$EW" -v PP="$PP" -v MC="$MC" -v FB="$FB" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    mp = (MP - 4) / 2;
    ew = (EW - 12) / 4;
    pp = (PP - 25) / 10;
    mc = (MC - 35) / 15;
    fb = (FB - 27.5) / 12.5;
    eng = 6.0 + 0.5*mp + 0.3*ew + 0.8*pp + 0.4*mc + 0.3*fb + 0.2*mp*ew + 0.15*pp*mc;
    alert = 5.5 + 0.4*mp - 0.3*ew + 0.6*pp + 0.8*mc + 0.2*fb + 0.2*pp*fb - 0.3*ew*mc;
    if (eng < 1) eng = 1; if (eng > 10) eng = 10;
    if (alert < 1) alert = 1; if (alert > 10) alert = 10;
    printf "{\"energy_score\": %.1f, \"afternoon_alertness\": %.1f}", eng + n1*0.4, alert + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

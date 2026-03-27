#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Rainwater Harvesting System
set -euo pipefail

OUTFILE=""
TK=""
GA=""
FF=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --tank_liters) TK="$2"; shift 2 ;;
        --gutter_area_m2) GA="$2"; shift 2 ;;
        --first_flush_L) FF="$2"; shift 2 ;;
        --annual_rainfall_mm) shift 2 ;;
        --usage_L_day) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$TK" ] || [ -z "$GA" ] || [ -z "$FF" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v TK="$TK" -v GA="$GA" -v FF="$FF" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    tk = (TK - 2750) / 2250;
    ga = (GA - 125) / 75;
    ff = (FF - 45) / 35;
    cap = 55 + 15*tk + 10*ga - 5*ff - 5*tk*tk - 3*ga*ga + 3*tk*ga;
    over = 30 - 12*tk - 5*ga + 3*ff + 4*tk*tk + 2*ga*ga - 2*tk*ga;
    if (cap < 10) cap = 10; if (cap > 95) cap = 95;
    if (over < 2) over = 2;
    printf "{\"capture_pct\": %.1f, \"overflow_pct\": %.1f}", cap + n1*3, over + n2*2;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

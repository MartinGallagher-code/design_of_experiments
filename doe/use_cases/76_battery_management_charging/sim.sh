#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Battery Management Charging
set -euo pipefail

OUTFILE=""
CC=""
CV=""
TC=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --charge_current_ma) CC="$2"; shift 2 ;;
        --cv_threshold_mv) CV="$2"; shift 2 ;;
        --trickle_cutoff_mv) TC="$2"; shift 2 ;;
        *) shift ;;
    esac
done

if [[ -z "$OUTFILE" ]] || [ -z "$CC" ] || [ -z "$CV" ] || [ -z "$TC" ]; then
    echo "ERROR: missing required arguments" >&2
    exit 1
fi

RESULT=$(awk -v CC="$CC" -v CV="$CV" -v TC="$TC" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    cc = (CC - 1750) / 1250;
    cv = (CV - 3525) / 125;
    tc = (TC - 2900) / 100;
    ct = 90 - 30*cc + 10*cv + 5*tc + 8*cc*cc + 3*cv*cv + 2*cc*cv;
    cyc = 2000 - 400*cc - 300*cv + 100*tc + 150*cc*cc + 80*cv*cv - 50*cc*cv + 30*tc*tc;
    if (ct < 15) ct = 15; if (cyc < 200) cyc = 200;
    printf "{\"charge_time_min\": %.0f, \"cycle_life_count\": %.0f}", ct + n1*5, cyc + n2*100;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Table Saw Cut Quality
set -euo pipefail

OUTFILE=""
BR=""
FR=""
TC=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --blade_rpm) BR="$2"; shift 2 ;;
        --feed_rate) FR="$2"; shift 2 ;;
        --tooth_count) TC="$2"; shift 2 ;;
        --blade_diam) shift 2 ;;
        --material) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$BR" ] || [ -z "$FR" ] || [ -z "$TC" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v BR="$BR" -v FR="$FR" -v TC="$TC" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    br = (BR - 4000) / 1000; fr = (FR - 3) / 2; tc = (TC - 52) / 28;
    smooth = 6.5 + 0.8*br - 1.0*fr + 1.5*tc - 0.3*br*br - 0.2*fr*fr - 0.4*tc*tc + 0.3*br*tc;
    tear = 4.0 - 0.5*br + 1.2*fr - 1.0*tc + 0.2*br*br + 0.3*fr*fr + 0.2*tc*tc + 0.3*fr*tc;
    if (smooth < 1) smooth = 1; if (smooth > 10) smooth = 10;
    if (tear < 1) tear = 1; if (tear > 10) tear = 10;
    printf "{\"smoothness\": %.1f, \"tearout_score\": %.1f}", smooth + n1*0.3, tear + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

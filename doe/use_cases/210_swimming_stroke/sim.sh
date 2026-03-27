#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Swimming Stroke Efficiency
set -euo pipefail

OUTFILE=""
SR=""
SL=""
KR=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --stroke_rate) SR="$2"; shift 2 ;;
        --stroke_length_m) SL="$2"; shift 2 ;;
        --kick_ratio) KR="$2"; shift 2 ;;
        --stroke) shift 2 ;;
        --pool) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$SR" ] || [ -z "$SL" ] || [ -z "$KR" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v SR="$SR" -v SL="$SL" -v KR="$KR" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    sr = (SR - 55) / 15; sl = (SL - 2) / 0.5; kr = (KR - 4) / 2;
    spd = 1.5 + 0.15*sr + 0.2*sl + 0.05*kr - 0.05*sr*sr - 0.08*sl*sl + 0.03*sr*sl;
    eng = 30 + 3*sr - 4*sl + 2*kr + 1*sr*sr + 0.5*sl*sl + 0.8*kr*kr + 0.5*sr*kr;
    if (spd < 0.8) spd = 0.8; if (eng < 15) eng = 15;
    printf "{\"speed_m_s\": %.2f, \"energy_kj_100m\": %.0f}", spd + n1*0.03, eng + n2*1.5;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

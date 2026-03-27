#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Sewing Machine Stitch Quality
set -euo pipefail

OUTFILE=""
UT=""
SL=""
FP=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --upper_tension) UT="$2"; shift 2 ;;
        --stitch_length_mm) SL="$2"; shift 2 ;;
        --foot_pressure) FP="$2"; shift 2 ;;
        --machine) shift 2 ;;
        --fabric) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$UT" ] || [ -z "$SL" ] || [ -z "$FP" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v UT="$UT" -v SL="$SL" -v FP="$FP" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    ut = (UT - 4.5) / 2.5; sl = (SL - 2.75) / 1.25; fp = (FP - 3) / 2;
    qual = 7.0 + 0.3*ut + 0.5*sl + 0.4*fp - 0.8*ut*ut - 0.3*sl*sl - 0.3*fp*fp + 0.2*ut*fp;
    brk = 0.5 + 0.5*ut - 0.2*sl + 0.3*fp + 0.4*ut*ut + 0.1*fp*fp + 0.2*ut*fp;
    if (qual < 1) qual = 1; if (qual > 10) qual = 10;
    if (brk < 0) brk = 0;
    printf "{\"stitch_quality\": %.1f, \"break_rate\": %.2f}", qual + n1*0.3, brk + n2*0.1;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

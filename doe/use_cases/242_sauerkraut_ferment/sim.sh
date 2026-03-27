#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Sauerkraut Fermentation
set -euo pipefail

OUTFILE=""
SP=""
SW=""
TP=""
WT=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --salt_pct) SP="$2"; shift 2 ;;
        --shred_mm) SW="$2"; shift 2 ;;
        --temp_c) TP="$2"; shift 2 ;;
        --weight_kg) WT="$2"; shift 2 ;;
        --cabbage) shift 2 ;;
        --vessel) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$SP" ] || [ -z "$SW" ] || [ -z "$TP" ] || [ -z "$WT" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v SP="$SP" -v SW="$SW" -v TP="$TP" -v WT="$WT" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    sp = (SP - 3) / 1; sw = (SW - 4) / 2; tp = (TP - 20) / 5; wt = (WT - 3) / 2;
    tang = 6.0 + 0.3*sp + 0.2*sw + 0.8*tp + 0.3*wt - 0.3*sp*sp - 0.2*tp*tp + 0.2*tp*wt;
    crunch = 6.5 + 0.5*sp + 0.8*sw - 0.5*tp - 0.2*wt - 0.2*sp*sp - 0.3*sw*sw + 0.2*sp*sw;
    if (tang < 1) tang = 1; if (tang > 10) tang = 10;
    if (crunch < 1) crunch = 1; if (crunch > 10) crunch = 10;
    printf "{\"tang_score\": %.1f, \"crunch_score\": %.1f}", tang + n1*0.3, crunch + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

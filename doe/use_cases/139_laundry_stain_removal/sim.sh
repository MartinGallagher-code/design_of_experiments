#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Laundry Stain Removal
set -euo pipefail

OUTFILE=""
WT=""
DD=""
SM=""
AG=""
BL=""
SR=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --water_temp_c) WT="$2"; shift 2 ;;
        --detergent_ml) DD="$2"; shift 2 ;;
        --soak_min) SM="$2"; shift 2 ;;
        --agitation) AG="$2"; shift 2 ;;
        --bleach_ml) BL="$2"; shift 2 ;;
        --spin_rpm) SR="$2"; shift 2 ;;
        --load_size) shift 2 ;;
        --fabric) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$WT" ] || [ -z "$DD" ] || [ -z "$SM" ] || [ -z "$AG" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v WT="$WT" -v DD="$DD" -v SM="$SM" -v AG="$AG" -v BL="$BL" -v SR="$SR" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    wt = (WT - 40) / 20;
    dd = (DD - 37.5) / 22.5;
    sm = (SM - 15) / 15;
    ag = (AG - 3) / 2;
    bl = (BL - 15) / 15;
    sr = (SR - 1000) / 400;
    stain = 70 + 8*wt + 6*dd + 5*sm + 4*ag + 7*bl + 1*sr + 2*wt*bl;
    wear = 3 + 0.8*wt + 0.3*dd + 0.2*sm + 1.2*ag + 0.5*bl + 0.6*sr + 0.3*ag*sr;
    if (stain > 100) stain = 100; if (stain < 30) stain = 30;
    if (wear < 1) wear = 1; if (wear > 10) wear = 10;
    printf "{\"stain_removal_pct\": %.0f, \"fabric_wear\": %.1f}", stain + n1*3, wear + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

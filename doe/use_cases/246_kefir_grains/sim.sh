#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Kefir Grain Cultivation
set -euo pipefail

OUTFILE=""
FP=""
FH=""
GR=""
TP=""
AG=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --fat_pct) FP="$2"; shift 2 ;;
        --ferm_hrs) FH="$2"; shift 2 ;;
        --grain_ratio_pct) GR="$2"; shift 2 ;;
        --temp_c) TP="$2"; shift 2 ;;
        --agitation) AG="$2"; shift 2 ;;
        --milk_type) shift 2 ;;
        --vessel) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$FP" ] || [ -z "$FH" ] || [ -z "$GR" ] || [ -z "$TP" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v FP="$FP" -v FH="$FH" -v GR="$GR" -v TP="$TP" -v AG="$AG" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    fp = (FP - 2.25) / 1.75; fh = (FH - 30) / 18; gr = (GR - 9) / 6; tp = (TP - 23) / 5; ag = (AG - 1.5) / 1.5;
    pro = 6.0 + 0.3*fp + 0.8*fh + 0.6*gr + 0.5*tp + 0.2*ag + 0.2*fh*gr;
    taste = 6.5 + 0.5*fp - 0.5*fh - 0.3*gr + 0.2*tp + 0.1*ag - 0.2*fh*fh + 0.1*fp*gr;
    if (pro < 1) pro = 1; if (pro > 10) pro = 10;
    if (taste < 1) taste = 1; if (taste > 10) taste = 10;
    printf "{\"probiotic_score\": %.1f, \"taste_score\": %.1f}", pro + n1*0.3, taste + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

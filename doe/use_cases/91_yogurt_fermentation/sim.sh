#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Yogurt Fermentation Optimization
set -euo pipefail

OUTFILE=""
FT=""
SP=""
FM=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --ferm_temp) FT="$2"; shift 2 ;;
        --starter_pct) SP="$2"; shift 2 ;;
        --ferm_time) FM="$2"; shift 2 ;;
        --milk_fat_pct) shift 2 ;;
        --pasteurization) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$FT" ] || [ -z "$SP" ] || [ -z "$FM" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v FT="$FT" -v SP="$SP" -v FM="$FM" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    ft = (FT - 41.5) / 4.5;
    sp = (SP - 3) / 2;
    fm = (FM - 8) / 4;
    pro = 8.5 + 0.6*ft + 0.8*sp + 1.2*fm - 0.3*ft*ft - 0.2*sp*sp - 0.4*fm*fm + 0.3*ft*sp;
    sour = 4.5 + 0.8*ft + 0.5*sp + 1.5*fm + 0.2*ft*ft + 0.3*fm*fm + 0.4*ft*fm;
    if (pro < 6) pro = 6; if (pro > 11) pro = 11;
    if (sour < 1) sour = 1; if (sour > 10) sour = 10;
    printf "{\"probiotic_cfu\": %.1f, \"sourness\": %.1f}", pro + n1*0.2, sour + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

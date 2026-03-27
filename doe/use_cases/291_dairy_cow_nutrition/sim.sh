#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Dairy Cow Feed Ration
set -euo pipefail
OUTFILE=""
FP=""
PP=""
EN=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --forage_pct) FP="$2"; shift 2 ;;
        --protein_pct) PP="$2"; shift 2 ;;
        --energy_mcal) EN="$2"; shift 2 ;;
        --breed) shift 2 ;;
        --lactation_stage) shift 2 ;;
        *) shift ;;
    esac
done
if [ -z "$FP" ] || [ -z "$PP" ] || [ -z "$EN" ]; then
    echo "Missing required factors" >&2; exit 1
fi
RESULT=$(awk -v FP="$FP" -v PP="$PP" -v EN="$EN" -v seed="$RANDOM" '
BEGIN {
    srand(seed); n1=(rand()-0.5)*2; n2=(rand()-0.5)*2;
    fp=(FP-55)/15;pp=(PP-17)/3;en=(EN-1.65)/0.15;
    milk=30-3*fp+2*pp+5*en-1*fp*fp-0.5*pp*pp-2*en*en+1*pp*en;
    cost=8-1*fp+1*pp+2*en+0.3*fp*fp+0.2*pp*en;
    if(milk<15)milk=15;if(cost<4)cost=4;
    printf "{\"milk_kg_day\": %.1f, \"feed_cost_day\": %.2f}",milk+n1*1,cost+n2*0.3;
}')
mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

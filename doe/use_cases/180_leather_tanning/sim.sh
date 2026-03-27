#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Leather Tanning Process
set -euo pipefail

OUTFILE=""
TN=""
SK=""
PH=""
FL=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --tannin_pct) TN="$2"; shift 2 ;;
        --soak_hrs) SK="$2"; shift 2 ;;
        --ph) PH="$2"; shift 2 ;;
        --fat_liquor_pct) FL="$2"; shift 2 ;;
        --hide_type) shift 2 ;;
        --method) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$TN" ] || [ -z "$SK" ] || [ -z "$PH" ] || [ -z "$FL" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v TN="$TN" -v SK="$SK" -v PH="$PH" -v FL="$FL" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    tn = (TN - 6.5) / 3.5; sk = (SK - 14) / 10; ph = (PH - 4) / 1; fl = (FL - 6.5) / 3.5;
    soft = 5.5 - 0.5*tn + 0.3*sk - 0.3*ph + 1.2*fl + 0.2*tn*tn + 0.1*sk*fl;
    color = 6.0 + 0.3*tn + 0.5*sk + 0.4*ph + 0.2*fl - 0.2*tn*tn - 0.3*sk*sk + 0.15*tn*sk;
    if (soft < 1) soft = 1; if (soft > 10) soft = 10;
    if (color < 1) color = 1; if (color > 10) color = 10;
    printf "{\"softness_score\": %.1f, \"color_uniformity\": %.1f}", soft + n1*0.3, color + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

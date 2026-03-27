#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Compost Maturity Optimization
set -euo pipefail

OUTFILE=""
CN=""
MP=""
TF=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --cn_ratio) CN="$2"; shift 2 ;;
        --moisture_pct) MP="$2"; shift 2 ;;
        --turn_freq) TF="$2"; shift 2 ;;
        --pile_volume) shift 2 ;;
        --initial_material) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$CN" ] || [ -z "$MP" ] || [ -z "$TF" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v CN="$CN" -v MP="$MP" -v TF="$TF" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    cn = (CN - 30) / 10;
    mp = (MP - 52.5) / 12.5;
    tf = (TF - 4) / 3;
    mat = 12 - 2*cn + 1.5*mp - 3*tf + 1*cn*cn + 0.5*mp*mp + 0.8*tf*tf - 0.5*cn*tf;
    nut = 6.0 + 0.8*cn + 0.5*mp + 0.6*tf - 0.4*cn*cn - 0.3*mp*mp + 0.3*cn*mp;
    if (mat < 3) mat = 3;
    if (nut < 1) nut = 1; if (nut > 10) nut = 10;
    printf "{\"maturity_weeks\": %.1f, \"nutrient_score\": %.1f}", mat + n1*1.0, nut + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

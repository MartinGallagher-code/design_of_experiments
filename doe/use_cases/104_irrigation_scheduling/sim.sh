#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Drip Irrigation Scheduling
set -euo pipefail

OUTFILE=""
DR=""
IH=""
ES=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --drip_rate) DR="$2"; shift 2 ;;
        --interval_hrs) IH="$2"; shift 2 ;;
        --emitter_spacing) ES="$2"; shift 2 ;;
        --crop) shift 2 ;;
        --season) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$DR" ] || [ -z "$IH" ] || [ -z "$ES" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v DR="$DR" -v IH="$IH" -v ES="$ES" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    dr = (DR - 2.5) / 1.5;
    ih = (IH - 27) / 21;
    es = (ES - 35) / 15;
    water = 25 + 8*dr - 6*ih - 3*es + 1.5*dr*dr + 2*ih*ih + 1*dr*ih;
    cyld = 2.5 + 0.5*dr - 0.8*ih - 0.3*es - 0.3*dr*dr - 0.5*ih*ih - 0.2*es*es + 0.2*dr*es;
    if (water < 5) water = 5;
    if (cyld < 0.5) cyld = 0.5;
    printf "{\"water_use_L\": %.1f, \"crop_yield\": %.2f}", water + n1*2, cyld + n2*0.15;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

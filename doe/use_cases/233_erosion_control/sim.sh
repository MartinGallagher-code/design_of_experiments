#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Hillside Erosion Control
set -euo pipefail

OUTFILE=""
MC=""
SD=""
TR=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --mulch_cm) MC="$2"; shift 2 ;;
        --seed_g_m2) SD="$2"; shift 2 ;;
        --terrace_m) TR="$2"; shift 2 ;;
        --slope_pct) shift 2 ;;
        --soil_type) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$MC" ] || [ -z "$SD" ] || [ -z "$TR" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v MC="$MC" -v SD="$SD" -v TR="$TR" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    mc = (MC - 6) / 4; sd = (SD - 30) / 20; tr = (TR - 12.5) / 7.5;
    loss = 12 - 4*mc - 2*sd - 3*tr + 1.5*mc*mc + 0.5*sd*sd + 1*tr*tr + 0.5*mc*tr;
    veg = 55 + 10*mc + 15*sd - 5*tr - 3*mc*mc - 4*sd*sd + 2*mc*sd;
    if (loss < 0.5) loss = 0.5; if (veg < 10) veg = 10; if (veg > 95) veg = 95;
    printf "{\"soil_loss_t_ha\": %.1f, \"vegetation_pct\": %.0f}", loss + n1*0.5, veg + n2*3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Aquaponics System Balance
set -euo pipefail

OUTFILE=""
FD=""
FR=""
FL=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --fish_density) FD="$2"; shift 2 ;;
        --feed_rate_pct) FR="$2"; shift 2 ;;
        --flow_rate_lph) FL="$2"; shift 2 ;;
        --fish_species) shift 2 ;;
        --plant) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$FD" ] || [ -z "$FR" ] || [ -z "$FL" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v FD="$FD" -v FR="$FR" -v FL="$FL" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    fd = (FD - 25) / 15;
    fr = (FR - 2.5) / 1.5;
    fl = (FL - 500) / 300;
    fish = 25 + 5*fd + 8*fr + 3*fl - 3*fd*fd - 2*fr*fr - 1*fl*fl + 2*fd*fr;
    plant = 80 + 15*fd + 20*fr + 10*fl - 8*fd*fd - 5*fr*fr - 3*fl*fl + 5*fd*fl;
    if (fish < 5) fish = 5;
    if (plant < 20) plant = 20;
    printf "{\"fish_growth_g\": %.1f, \"plant_yield_g\": %.0f}", fish + n1*2, plant + n2*5;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

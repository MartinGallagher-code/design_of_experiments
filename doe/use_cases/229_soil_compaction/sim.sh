#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Soil Compaction Testing
set -euo pipefail

OUTFILE=""
WP=""
BL=""
LY=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --water_pct) WP="$2"; shift 2 ;;
        --blows_per_layer) BL="$2"; shift 2 ;;
        --layers) LY="$2"; shift 2 ;;
        --hammer_kg) shift 2 ;;
        --mold) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$WP" ] || [ -z "$BL" ] || [ -z "$LY" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v WP="$WP" -v BL="$BL" -v LY="$LY" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    wp = (WP - 14) / 6; bl = (BL - 35.5) / 20.5; ly = (LY - 4) / 1;
    dens = 1800 + 50*wp + 30*bl + 20*ly - 60*wp*wp - 10*bl*bl + 5*wp*bl;
    cbr = 15 - 3*wp + 5*bl + 3*ly + 4*wp*wp - 1*bl*bl + 1*wp*bl;
    if (dens < 1400) dens = 1400; if (cbr < 2) cbr = 2;
    printf "{\"dry_density_kg_m3\": %.0f, \"cbr_pct\": %.0f}", dens + n1*15, cbr + n2*1;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

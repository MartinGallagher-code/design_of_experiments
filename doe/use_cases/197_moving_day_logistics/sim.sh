#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Moving Day Logistics
set -euo pipefail

OUTFILE=""
BV=""
CS=""
PL=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --box_volume_L) BV="$2"; shift 2 ;;
        --crew_size) CS="$2"; shift 2 ;;
        --padding_layers) PL="$2"; shift 2 ;;
        --distance_km) shift 2 ;;
        --apartment_floor) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$BV" ] || [ -z "$CS" ] || [ -z "$PL" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v BV="$BV" -v CS="$CS" -v PL="$PL" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    bv = (BV - 55) / 25; cs = (CS - 4) / 2; pl = (PL - 2.5) / 1.5;
    hrs = 6 + 0.5*bv - 2*cs + 0.3*pl + 0.3*bv*bv + 0.5*cs*cs + 0.2*bv*cs;
    brk = 5 + 0.8*bv + 0.3*cs - 2*pl + 0.3*bv*bv + 0.5*pl*pl - 0.3*cs*pl;
    if (hrs < 2) hrs = 2;
    if (brk < 0) brk = 0; if (brk > 20) brk = 20;
    printf "{\"total_hours\": %.1f, \"breakage_pct\": %.1f}", hrs + n1*0.3, brk + n2*0.5;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

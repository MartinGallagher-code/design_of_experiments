#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Concert Hall Acoustic Design
set -euo pipefail

OUTFILE=""
CH=""
WR=""
AB=""
DI=""
SR=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --ceiling_m) CH="$2"; shift 2 ;;
        --width_ratio) WR="$2"; shift 2 ;;
        --absorption_nrc) AB="$2"; shift 2 ;;
        --diffusion_idx) DI="$2"; shift 2 ;;
        --stage_riser_m) SR="$2"; shift 2 ;;
        --seats) shift 2 ;;
        --floor_material) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$CH" ] || [ -z "$WR" ] || [ -z "$AB" ] || [ -z "$DI" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v CH="$CH" -v WR="$WR" -v AB="$AB" -v DI="$DI" -v SR="$SR" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    ch = (CH - 13) / 5;
    wr = (WR - 0.7) / 0.2;
    ab = (AB - 0.5) / 0.2;
    di = (DI - 0.5) / 0.3;
    sr = (SR - 0.75) / 0.45;
    c80 = 1.5 - 1.0*ch + 0.5*wr + 2.0*ab + 0.8*di + 0.3*sr + 0.3*ab*di;
    warm = 1.1 + 0.15*ch - 0.1*wr - 0.2*ab + 0.05*di + 0.08*sr + 0.05*ch*wr;
    if (c80 < -3) c80 = -3;
    if (warm < 0.6) warm = 0.6; if (warm > 1.6) warm = 1.6;
    printf "{\"clarity_c80\": %.1f, \"warmth_index\": %.2f}", c80 + n1*0.3, warm + n2*0.03;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

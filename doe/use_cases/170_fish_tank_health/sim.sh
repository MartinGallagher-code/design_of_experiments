#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Tropical Fish Tank Health
set -euo pipefail

OUTFILE=""
WC=""
FD=""
LH=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --water_change_pct) WC="$2"; shift 2 ;;
        --feed_g_day) FD="$2"; shift 2 ;;
        --light_hrs) LH="$2"; shift 2 ;;
        --tank_L) shift 2 ;;
        --fish_count) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$WC" ] || [ -z "$FD" ] || [ -z "$LH" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v WC="$WC" -v FD="$FD" -v LH="$LH" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    wc = (WC - 25) / 15; fd = (FD - 1.75) / 1.25; lh = (LH - 9) / 3;
    vit = 7.0 + 0.5*wc + 0.8*fd + 0.3*lh - 0.3*wc*wc - 0.5*fd*fd + 0.2*wc*fd;
    alg = 4.0 - 0.8*wc + 1.0*fd + 1.2*lh + 0.3*fd*fd + 0.2*lh*lh + 0.3*fd*lh;
    if (vit < 1) vit = 1; if (vit > 10) vit = 10;
    if (alg < 1) alg = 1; if (alg > 10) alg = 10;
    printf "{\"vitality_score\": %.1f, \"algae_level\": %.1f}", vit + n1*0.3, alg + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

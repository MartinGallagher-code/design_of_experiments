#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Hydroponic Nutrient Solution
set -euo pipefail

OUTFILE=""
N=""
P=""
K=""
PH=""
EC=""
CA=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --nitrogen_ppm) N="$2"; shift 2 ;;
        --phosphorus_ppm) P="$2"; shift 2 ;;
        --potassium_ppm) K="$2"; shift 2 ;;
        --ph_level) PH="$2"; shift 2 ;;
        --ec_level) EC="$2"; shift 2 ;;
        --calcium_ppm) CA="$2"; shift 2 ;;
        --crop) shift 2 ;;
        --system) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$N" ] || [ -z "$P" ] || [ -z "$K" ] || [ -z "$PH" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v N="$N" -v P="$P" -v K="$K" -v PH="$PH" -v EC="$EC" -v CA="$CA" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    n = (N - 175) / 75;
    p = (P - 55) / 25;
    k = (K - 250) / 100;
    ph = (PH - 6) / 0.5;
    ec = (EC - 1.75) / 0.75;
    ca = (CA - 175) / 75;
    gr = 3.5 + 0.8*n + 0.3*p + 0.5*k - 0.4*ph + 0.6*ec + 0.2*ca + 0.2*n*k + 0.15*ec*n;
    col = 7.0 + 1.0*n + 0.2*p + 0.3*k - 0.3*ph + 0.2*ec + 0.1*ca + 0.15*n*ph;
    if (gr < 0.5) gr = 0.5;
    if (col < 1) col = 1; if (col > 10) col = 10;
    printf "{\"growth_rate\": %.2f, \"color_score\": %.1f}", gr + n1*0.3, col + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Wine Tasting Panel (Box-Behnken with 3 blocks)
set -euo pipefail

OUTFILE=""
OA=""
SR=""
SL=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --oak_aging) OA="$2"; shift 2 ;;
        --sugar_residual) SR="$2"; shift 2 ;;
        --sulfite_level) SL="$2"; shift 2 ;;
        --grape_variety) shift 2 ;;
        --vintage) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$OA" ] || [ -z "$SR" ] || [ -z "$SL" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v OA="$OA" -v SR="$SR" -v SL="$SL" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    # Normalize factors to [-1, 1]
    oa = (OA - 10.5) / 7.5;
    sr = (SR - 4.5) / 3.5;
    sl = (SL - 40) / 20;

    # Aroma: improves with aging, moderate sugar, harmed by excess sulfite
    aroma = 7.0 + 1.2*oa + 0.4*sr - 0.6*sl - 0.5*oa*oa - 0.3*sr*sr - 0.2*sl*sl + 0.15*oa*sr;
    aroma = aroma + n1 * 0.3;
    if (aroma < 1) aroma = 1;
    if (aroma > 10) aroma = 10;

    # Balance: peaks at moderate values, strong quadratic effects
    bal = 7.5 + 0.3*oa + 0.5*sr - 0.4*sl - 0.7*oa*oa - 0.6*sr*sr - 0.3*sl*sl + 0.1*oa*sl - 0.2*sr*sl;
    bal = bal + n2 * 0.25;
    if (bal < 1) bal = 1;
    if (bal > 10) bal = 10;

    printf "{\"aroma_score\": %.1f, \"balance_score\": %.1f}", aroma, bal;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

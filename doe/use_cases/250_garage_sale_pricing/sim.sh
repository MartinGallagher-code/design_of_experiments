#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Garage Sale Pricing Strategy
set -euo pipefail

OUTFILE=""
PM=""
DH=""
SG=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --price_multiplier) PM="$2"; shift 2 ;;
        --discount_per_hr_pct) DH="$2"; shift 2 ;;
        --signs) SG="$2"; shift 2 ;;
        --duration) shift 2 ;;
        --items) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$PM" ] || [ -z "$DH" ] || [ -z "$SG" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v PM="$PM" -v DH="$DH" -v SG="$SG" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    pm = (PM - 0.25) / 0.15; dh = (DH - 7.5) / 7.5; sg = (SG - 6) / 4;
    rev = 350 + 60*pm - 30*dh + 40*sg - 40*pm*pm - 10*dh*dh + 10*pm*dh + 5*pm*sg;
    unsold = 30 + 10*pm - 8*dh - 5*sg + 5*pm*pm + 2*dh*dh + 2*pm*dh;
    if (rev < 50) rev = 50; if (unsold < 5) unsold = 5; if (unsold > 70) unsold = 70;
    printf "{\"revenue_usd\": %.0f, \"unsold_pct\": %.0f}", rev + n1*15, unsold + n2*2;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

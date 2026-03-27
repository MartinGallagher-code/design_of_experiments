#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Golf Driver Launch Conditions
set -euo pipefail

OUTFILE=""
LO=""
SF=""
TH=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --loft_deg) LO="$2"; shift 2 ;;
        --shaft_flex) SF="$2"; shift 2 ;;
        --tee_height_mm) TH="$2"; shift 2 ;;
        --swing_speed) shift 2 ;;
        --ball) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$LO" ] || [ -z "$SF" ] || [ -z "$TH" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v LO="$LO" -v SF="$SF" -v TH="$TH" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    lo = (LO - 10) / 2; sf = (SF - 3) / 2; th = (TH - 55) / 15;
    carry = 240 + 5*lo + 3*sf + 4*th - 3*lo*lo - 2*sf*sf - 1.5*th*th + 1*lo*th;
    spin = 500 + 100*lo + 150*sf + 50*th + 50*lo*lo + 80*sf*sf + 30*lo*sf;
    if (carry < 180) carry = 180; if (spin < 50) spin = 50;
    printf "{\"carry_yards\": %.0f, \"side_spin_rpm\": %.0f}", carry + n1*5, spin + n2*30;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

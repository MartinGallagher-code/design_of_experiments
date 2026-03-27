#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Interior Paint Finish Quality
set -euo pipefail

OUTFILE=""
CM=""
HP=""
DP=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --coat_mils) CM="$2"; shift 2 ;;
        --humidity_pct) HP="$2"; shift 2 ;;
        --dilution_pct) DP="$2"; shift 2 ;;
        --paint_type) shift 2 ;;
        --surface) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$CM" ] || [ -z "$HP" ] || [ -z "$DP" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v CM="$CM" -v HP="$HP" -v DP="$DP" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    cm = (CM - 5.5) / 2.5;
    hp = (HP - 50) / 20;
    dp = (DP - 7.5) / 7.5;
    cov = 7.0 + 1.5*cm - 0.3*hp - 0.8*dp - 0.4*cm*cm + 0.2*cm*hp;
    dry = 45 + 10*cm + 15*hp + 5*dp + 3*cm*hp + 2*hp*dp;
    if (cov < 1) cov = 1; if (cov > 10) cov = 10;
    if (dry < 15) dry = 15;
    printf "{\"coverage_score\": %.1f, \"dry_time_min\": %.0f}", cov + n1*0.3, dry + n2*4;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

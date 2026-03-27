#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Reptile Terrarium Setup
set -euo pipefail

OUTFILE=""
BK=""
HM=""
UV=""
SB=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --basking_c) BK="$2"; shift 2 ;;
        --humidity_pct) HM="$2"; shift 2 ;;
        --uvb_pct) UV="$2"; shift 2 ;;
        --substrate_cm) SB="$2"; shift 2 ;;
        --species) shift 2 ;;
        --enclosure_L) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$BK" ] || [ -z "$HM" ] || [ -z "$UV" ] || [ -z "$SB" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v BK="$BK" -v HM="$HM" -v UV="$UV" -v SB="$SB" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    bk = (BK - 35) / 5; hm = (HM - 50) / 20; uv = (UV - 9.5) / 4.5; sb = (SB - 9) / 6;
    act = 6.0 + 0.5*bk + 0.3*hm + 0.6*uv + 0.4*sb - 0.8*bk*bk - 0.3*hm*hm + 0.2*bk*uv;
    stress = 4.0 + 0.8*bk - 0.3*hm + 0.2*uv - 0.3*sb + 0.5*bk*bk + 0.2*hm*hm;
    if (act < 1) act = 1; if (act > 10) act = 10;
    if (stress < 1) stress = 1; if (stress > 10) stress = 10;
    printf "{\"activity_score\": %.1f, \"stress_indicators\": %.1f}", act + n1*0.3, stress + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

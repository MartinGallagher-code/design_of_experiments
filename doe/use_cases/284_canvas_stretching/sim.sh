#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Canvas Stretching Tension
set -euo pipefail
OUTFILE=""
SS=""
BT=""
CG=""
PP=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --staple_spacing_cm) SS="$2"; shift 2 ;;
        --bar_mm) BT="$2"; shift 2 ;;
        --canvas_gsm) CG="$2"; shift 2 ;;
        --pre_prime) PP="$2"; shift 2 ;;
        --size) shift 2 ;;
        --canvas) shift 2 ;;
        *) shift ;;
    esac
done
if [ -z "$SS" ] || [ -z "$BT" ] || [ -z "$CG" ] || [ -z "$PP" ]; then
    echo "Missing required factors" >&2; exit 1
fi
RESULT=$(awk -v SS="$SS" -v BT="$BT" -v CG="$CG" -v PP="$PP" -v seed="$RANDOM" '
BEGIN {
    srand(seed); n1=(rand()-0.5)*2; n2=(rand()-0.5)*2;
    ss=(SS-5.5)/2.5;bt=(BT-29)/11;cg=(CG-300)/100;pp=(PP=="gesso")?1:-1;
    flat=7-0.8*ss+0.5*bt+0.3*cg+0.3*pp-0.3*ss*ss-0.2*bt*bt+0.2*ss*bt;
    warp=3+0.5*ss-0.8*bt+0.3*cg-0.2*pp+0.2*ss*ss+0.3*bt*bt-0.1*bt*cg;
    if(flat<1)flat=1;if(flat>10)flat=10;if(warp<0.5)warp=0.5;
    printf "{\"flatness\": %.1f, \"warp_mm\": %.1f}",flat+n1*0.3,warp+n2*0.2;
}')
mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

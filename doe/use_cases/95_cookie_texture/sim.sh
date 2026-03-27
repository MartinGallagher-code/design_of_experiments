#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Cookie Texture Optimization
set -euo pipefail

OUTFILE=""
BP=""
BS=""
EG=""
BK=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --butter_pct) BP="$2"; shift 2 ;;
        --brown_sugar_ratio) BS="$2"; shift 2 ;;
        --eggs) EG="$2"; shift 2 ;;
        --bake_time) BK="$2"; shift 2 ;;
        --oven_temp) shift 2 ;;
        --flour_type) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$BP" ] || [ -z "$BS" ] || [ -z "$EG" ] || [ -z "$BK" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v BP="$BP" -v BS="$BS" -v EG="$EG" -v BK="$BK" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    bp = (BP - 40) / 10;
    bs = (BS - 50) / 50;
    eg = (EG - 2) / 1;
    bt = (BK - 11) / 3;
    chew = 6.0 + 0.8*bp + 1.2*bs + 0.6*eg - 1.5*bt - 0.5*bp*bp - 0.3*bs*bs + 0.4*bp*bs - 0.5*eg*bt;
    spread = 3.5 + 0.5*bp - 0.3*bs - 0.4*eg + 0.6*bt + 0.2*bp*bt - 0.1*bs*eg;
    if (chew < 1) chew = 1; if (chew > 10) chew = 10;
    if (spread < 1.5) spread = 1.5; if (spread > 6) spread = 6;
    printf "{\"chewiness_score\": %.1f, \"spread_ratio\": %.2f}", chew + n1*0.4, spread + n2*0.2;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

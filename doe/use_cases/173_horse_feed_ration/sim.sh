#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Horse Feed Ration Balance
set -euo pipefail

OUTFILE=""
HY=""
GR=""
MN=""
OL=""
FF=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --hay_kg) HY="$2"; shift 2 ;;
        --grain_kg) GR="$2"; shift 2 ;;
        --mineral_g) MN="$2"; shift 2 ;;
        --oil_ml) OL="$2"; shift 2 ;;
        --feed_freq) FF="$2"; shift 2 ;;
        --horse_weight) shift 2 ;;
        --activity) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$HY" ] || [ -z "$GR" ] || [ -z "$MN" ] || [ -z "$OL" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v HY="$HY" -v GR="$GR" -v MN="$MN" -v OL="$OL" -v FF="$FF" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    hy = (HY - 9) / 3; gr = (GR - 3) / 2; mn = (MN - 60) / 30; ol = (OL - 60) / 60; ff = (FF - 3) / 1;
    body = 5.5 + 0.5*hy + 0.8*gr + 0.2*mn + 0.3*ol + 0.2*ff - 0.3*gr*gr + 0.1*hy*gr;
    hoof = 6.0 + 0.2*hy + 0.1*gr + 0.6*mn + 0.4*ol + 0.15*ff + 0.1*mn*ol;
    if (body < 1) body = 1; if (body > 9) body = 9;
    if (hoof < 1) hoof = 1; if (hoof > 10) hoof = 10;
    printf "{\"body_condition\": %.1f, \"hoof_quality\": %.1f}", body + n1*0.3, hoof + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

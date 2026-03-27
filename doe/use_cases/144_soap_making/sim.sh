#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Handmade Soap Formulation
set -euo pipefail

OUTFILE=""
CO=""
OL=""
LY=""
EO=""
CW=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --coconut_pct) CO="$2"; shift 2 ;;
        --olive_pct) OL="$2"; shift 2 ;;
        --lye_concentration) LY="$2"; shift 2 ;;
        --essential_oil_pct) EO="$2"; shift 2 ;;
        --cure_weeks) CW="$2"; shift 2 ;;
        --superfat_pct) shift 2 ;;
        --method) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$CO" ] || [ -z "$OL" ] || [ -z "$LY" ] || [ -z "$EO" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v CO="$CO" -v OL="$OL" -v LY="$LY" -v EO="$EO" -v CW="$CW" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    co = (CO - 27.5) / 12.5;
    ol = (OL - 50) / 20;
    ly = (LY - 33) / 5;
    eo = (EO - 2.5) / 1.5;
    cw = (CW - 6) / 2;
    lath = 5.5 + 1.5*co - 0.5*ol + 0.3*ly + 0.2*eo + 0.4*cw + 0.3*co*ly;
    hard = 5.0 + 1.0*co - 0.8*ol + 0.5*ly - 0.1*eo + 0.8*cw + 0.2*co*cw;
    if (lath < 1) lath = 1; if (lath > 10) lath = 10;
    if (hard < 1) hard = 1; if (hard > 10) hard = 10;
    printf "{\"lather_score\": %.1f, \"hardness_score\": %.1f}", lath + n1*0.4, hard + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

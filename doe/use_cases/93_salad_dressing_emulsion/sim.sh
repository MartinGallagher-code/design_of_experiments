#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Salad Dressing Emulsion Stability
set -euo pipefail

OUTFILE=""
OR=""
VA=""
MG=""
EY=""
BS=""
MT=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --oil_ratio) OR="$2"; shift 2 ;;
        --vinegar_acidity) VA="$2"; shift 2 ;;
        --mustard_g) MG="$2"; shift 2 ;;
        --egg_yolk_count) EY="$2"; shift 2 ;;
        --blend_speed) BS="$2"; shift 2 ;;
        --mix_temp) MT="$2"; shift 2 ;;
        --total_volume_ml) shift 2 ;;
        --salt_g) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$OR" ] || [ -z "$VA" ] || [ -z "$MG" ] || [ -z "$EY" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v OR="$OR" -v VA="$VA" -v MG="$MG" -v EY="$EY" -v BS="$BS" -v MT="$MT" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    or_ = (OR - 65) / 15;
    va = (VA - 5.5) / 1.5;
    mg = (MG - 8.5) / 6.5;
    ey = (EY - 1.5) / 1.5;
    bs = (BS - 12500) / 7500;
    mt = (MT - 15) / 10;
    stab = 48 + 10*or_ + 5*va + 12*mg + 15*ey + 8*bs - 6*mt + 3*mg*ey + 2*or_*bs;
    taste = 6.5 - 0.3*or_ + 0.8*va + 0.5*mg + 0.4*ey - 0.2*bs + 0.3*mt + 0.2*va*mg;
    if (stab < 1) stab = 1;
    if (taste < 1) taste = 1; if (taste > 10) taste = 10;
    printf "{\"stability_hrs\": %.0f, \"taste_score\": %.1f}", stab + n1*5, taste + n2*0.4;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

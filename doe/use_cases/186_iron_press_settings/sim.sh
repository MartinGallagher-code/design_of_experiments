#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Garment Pressing Settings
set -euo pipefail

OUTFILE=""
IT=""
SG=""
PS=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --iron_temp_c) IT="$2"; shift 2 ;;
        --steam_g_min) SG="$2"; shift 2 ;;
        --press_sec) PS="$2"; shift 2 ;;
        --fabric) shift 2 ;;
        --press_cloth) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$IT" ] || [ -z "$SG" ] || [ -z "$PS" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v IT="$IT" -v SG="$SG" -v PS="$PS" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    it = (IT - 155) / 45; sg = (SG - 20) / 20; ps = (PS - 9) / 6;
    crease = 5.5 + 1.2*it + 0.8*sg + 0.6*ps - 0.3*it*it - 0.2*sg*sg + 0.2*it*sg;
    shine = 3.0 + 1.5*it + 0.3*sg + 0.8*ps + 0.5*it*it + 0.2*ps*ps + 0.3*it*ps;
    if (crease < 1) crease = 1; if (crease > 10) crease = 10;
    if (shine < 1) shine = 1; if (shine > 10) shine = 10;
    printf "{\"crease_sharpness\": %.1f, \"shine_risk\": %.1f}", crease + n1*0.3, shine + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

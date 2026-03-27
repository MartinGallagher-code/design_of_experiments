#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Perfume Longevity & Sillage
set -euo pipefail

OUTFILE=""
AL=""
FX=""
SP=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --alcohol_pct) AL="$2"; shift 2 ;;
        --fixative_pct) FX="$2"; shift 2 ;;
        --sprays) SP="$2"; shift 2 ;;
        --fragrance_type) shift 2 ;;
        --notes) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$AL" ] || [ -z "$FX" ] || [ -z "$SP" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v AL="$AL" -v FX="$FX" -v SP="$SP" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    al = (AL - 72.5) / 12.5; fx = (FX - 3) / 2; sp = (SP - 5) / 3;
    long = 6 - 1*al + 2*fx + 1.5*sp + 0.3*al*al - 0.5*fx*fx + 0.3*fx*sp;
    sil = 5.5 - 0.5*al + 0.8*fx + 1.2*sp - 0.3*al*al - 0.3*fx*fx - 0.4*sp*sp + 0.2*fx*sp;
    if (long < 1) long = 1; if (sil < 1) sil = 1; if (sil > 10) sil = 10;
    printf "{\"longevity_hrs\": %.1f, \"sillage_score\": %.1f}", long + n1*0.5, sil + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

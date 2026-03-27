#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Guitar String Tone Optimization
set -euo pipefail

OUTFILE=""
GA=""
AC=""
PK=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --gauge_thou) GA="$2"; shift 2 ;;
        --action_mm) AC="$2"; shift 2 ;;
        --pickup_mm) PK="$2"; shift 2 ;;
        --guitar_type) shift 2 ;;
        --tuning) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$GA" ] || [ -z "$AC" ] || [ -z "$PK" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v GA="$GA" -v AC="$AC" -v PK="$PK" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    ga = (GA - 11) / 2;
    ac = (AC - 2.25) / 0.75;
    pk = (PK - 3.5) / 1.5;
    bright = 6.5 - 1.2*ga + 0.5*ac - 0.8*pk + 0.3*ga*ga + 0.2*ac*pk;
    sust = 4.0 + 0.8*ga + 0.5*ac + 0.3*pk - 0.3*ga*ga - 0.2*ac*ac + 0.2*ga*ac;
    if (bright < 1) bright = 1; if (bright > 10) bright = 10;
    if (sust < 1) sust = 1;
    printf "{\"brightness\": %.1f, \"sustain_sec\": %.1f}", bright + n1*0.3, sust + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Tennis Racket String Setup
set -euo pipefail

OUTFILE=""
MT=""
CT=""
GA=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --main_tension_kg) MT="$2"; shift 2 ;;
        --cross_tension_kg) CT="$2"; shift 2 ;;
        --gauge_mm) GA="$2"; shift 2 ;;
        --racket) shift 2 ;;
        --string_material) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$MT" ] || [ -z "$CT" ] || [ -z "$GA" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v MT="$MT" -v CT="$CT" -v GA="$GA" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    mt = (MT - 24) / 4; ct = (CT - 22) / 4; ga = (GA - 1.25) / 0.1;
    pwr = 6.5 - 1.0*mt - 0.5*ct - 0.8*ga - 0.3*mt*mt + 0.2*ct*ct + 0.2*mt*ct;
    ctrl = 5.5 + 0.8*mt + 0.5*ct + 0.3*ga - 0.4*mt*mt - 0.2*ct*ct + 0.2*mt*ga;
    if (pwr < 1) pwr = 1; if (pwr > 10) pwr = 10;
    if (ctrl < 1) ctrl = 1; if (ctrl > 10) ctrl = 10;
    printf "{\"power_score\": %.1f, \"control_score\": %.1f}", pwr + n1*0.3, ctrl + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

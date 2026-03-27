#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Titration Accuracy Optimization
set -euo pipefail

OUTFILE=""
DS=""
SR=""
IC=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --drop_size_ul) DS="$2"; shift 2 ;;
        --stir_rpm) SR="$2"; shift 2 ;;
        --indicator_pct) IC="$2"; shift 2 ;;
        --analyte) shift 2 ;;
        --titrant) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$DS" ] || [ -z "$SR" ] || [ -z "$IC" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v DS="$DS" -v SR="$SR" -v IC="$IC" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    ds = (DS - 55) / 45; sr = (SR - 350) / 250; ic = (IC - 0.275) / 0.225;
    prec = 96 - 2*ds + 0.5*sr + 1*ic + 1*ds*ds - 0.3*sr*sr - 0.5*ic*ic + 0.3*sr*ic;
    waste = 0.5 + 0.3*ds - 0.1*sr - 0.05*ic + 0.1*ds*ds;
    if (prec < 80) prec = 80; if (prec > 100) prec = 100;
    if (waste < 0.02) waste = 0.02;
    printf "{\"precision_pct\": %.1f, \"reagent_waste_ml\": %.2f}", prec + n1*0.5, waste + n2*0.03;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

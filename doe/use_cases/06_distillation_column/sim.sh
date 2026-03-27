#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated distillation column — CCD star points produce values outside [low, high].
#
# Model (hidden):
#   separation_efficiency ~ 85 + 6*rr_c + 2*fr_c + 4*cp_c - 3*rr_c^2 - 2*fr_c^2 - 1.5*cp_c^2 + 1.5*rr_c*cp_c + noise
#   energy_cost ~ 30 + 10*rr_c + 5*fr_c + 3*cp_c + 2*rr_c*fr_c + noise
#
# Coded: rr_c = (rr - 3.0)/1.5, fr_c = (fr - 100)/50, cp_c = (cp - 2.0)/1.0

set -euo pipefail

OUTFILE=""
RR="" FR="" CP=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out)             OUTFILE="$2"; shift 2 ;;
        --reflux_ratio)    RR="$2";      shift 2 ;;
        --feed_rate)       FR="$2";      shift 2 ;;
        --column_pressure) CP="$2";      shift 2 ;;
        --feed_temp|--n_trays) shift 2 ;;
        *)                 shift ;;
    esac
done

if [[ -z "$OUTFILE" ]]; then
    echo "Error: --out <path> is required" >&2
    exit 1
fi

RESULT=$(awk -v rr="$RR" -v fr="$FR" -v cp="$CP" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 3;
    n2 = (rand() - 0.5) * 4;

    rr_c = (rr - 3.0) / 1.5;
    fr_c = (fr - 100) / 50;
    cp_c = (cp - 2.0) / 1.0;

    se = 85 + 6*rr_c + 2*fr_c + 4*cp_c - 3*rr_c*rr_c - 2*fr_c*fr_c - 1.5*cp_c*cp_c + 1.5*rr_c*cp_c + n1;
    if (se > 100) se = 100;
    if (se < 30) se = 30;

    ec = 30 + 10*rr_c + 5*fr_c + 3*cp_c + 2*rr_c*fr_c + n2;
    if (ec < 5) ec = 5;

    printf "{\"separation_efficiency\": %.2f, \"energy_cost\": %.2f}", se, ec;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

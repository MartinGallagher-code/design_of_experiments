#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Mineral Flotation Separation
set -euo pipefail

OUTFILE=""
CL=""
FR=""
PH=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --collector_g_t) CL="$2"; shift 2 ;;
        --frother_g_t) FR="$2"; shift 2 ;;
        --pulp_ph) PH="$2"; shift 2 ;;
        --mineral) shift 2 ;;
        --grind_size) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$CL" ] || [ -z "$FR" ] || [ -z "$PH" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v CL="$CL" -v FR="$FR" -v PH="$PH" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    cl = (CL - 50) / 30; fr = (FR - 25) / 15; ph = (PH - 9) / 2;
    rec = 75 + 8*cl + 4*fr + 3*ph - 5*cl*cl - 3*fr*fr - 2*ph*ph + 2*cl*fr;
    grade = 22 - 3*cl - 1*fr + 2*ph + 2*cl*cl + 1*fr*fr - 1*ph*ph + 1*cl*ph;
    if (rec < 30) rec = 30; if (rec > 98) rec = 98;
    if (grade < 8) grade = 8; if (grade > 35) grade = 35;
    printf "{\"recovery_pct\": %.0f, \"grade_pct\": %.1f}", rec + n1*2, grade + n2*1;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

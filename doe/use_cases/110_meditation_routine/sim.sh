#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Meditation Routine Effectiveness
set -euo pipefail

OUTFILE=""
DM=""
TD=""
GP=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --duration_min) DM="$2"; shift 2 ;;
        --time_of_day) TD="$2"; shift 2 ;;
        --guided_pct) GP="$2"; shift 2 ;;
        --frequency) shift 2 ;;
        --environment) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$DM" ] || [ -z "$TD" ] || [ -z "$GP" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v DM="$DM" -v TD="$TD" -v GP="$GP" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    dm = (DM - 17.5) / 12.5;
    td = (TD - 14) / 8;
    gp = (GP - 50) / 50;
    stress = 5.5 + 1.5*dm - 0.3*td + 0.5*gp - 0.5*dm*dm + 0.2*td*td - 0.3*gp*gp + 0.3*dm*gp;
    focus = 5.0 + 1.2*dm - 0.5*td - 0.3*gp - 0.4*dm*dm + 0.3*td*td + 0.2*dm*td;
    if (stress < 1) stress = 1; if (stress > 10) stress = 10;
    if (focus < 1) focus = 1; if (focus > 10) focus = 10;
    printf "{\"stress_reduction\": %.1f, \"focus_score\": %.1f}", stress + n1*0.4, focus + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

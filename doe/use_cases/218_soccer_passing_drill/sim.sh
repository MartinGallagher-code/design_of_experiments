#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Soccer Passing Drill Design
set -euo pipefail

OUTFILE=""
PD=""
PC=""
TM=""
RS=""
CS=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --pass_dist_m) PD="$2"; shift 2 ;;
        --player_count) PC="$2"; shift 2 ;;
        --tempo_bpm) TM="$2"; shift 2 ;;
        --rest_sec) RS="$2"; shift 2 ;;
        --cone_spacing_m) CS="$2"; shift 2 ;;
        --ball_type) shift 2 ;;
        --surface) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$PD" ] || [ -z "$PC" ] || [ -z "$TM" ] || [ -z "$RS" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v PD="$PD" -v PC="$PC" -v TM="$TM" -v RS="$RS" -v CS="$CS" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    pd = (PD - 12.5) / 7.5; pc = (PC - 7) / 3; tm = (TM - 90) / 30; rs = (RS - 35) / 25; cs = (CS - 5) / 3;
    acc = 75 - 5*pd + 2*pc - 3*tm + 2*rs + 1*cs - 1*pd*pd + 0.5*pc*tm;
    dec = 800 + 50*pd + 30*pc + 80*tm - 40*rs - 20*cs + 20*pd*tm;
    if (acc < 40) acc = 40; if (acc > 100) acc = 100; if (dec < 300) dec = 300;
    printf "{\"accuracy_pct\": %.0f, \"decision_speed_ms\": %.0f}", acc + n1*3, dec + n2*30;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

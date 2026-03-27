#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Water Heater Efficiency
set -euo pipefail

OUTFILE=""
TS=""
TR=""
PI=""
RT=""
IT=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --thermostat_c) TS="$2"; shift 2 ;;
        --tank_r_value) TR="$2"; shift 2 ;;
        --pipe_insulation) PI="$2"; shift 2 ;;
        --recirc_timer) RT="$2"; shift 2 ;;
        --inlet_temp_c) IT="$2"; shift 2 ;;
        --tank_size_L) shift 2 ;;
        --household_size) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$TS" ] || [ -z "$TR" ] || [ -z "$PI" ] || [ -z "$RT" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v TS="$TS" -v TR="$TR" -v PI="$PI" -v RT="$RT" -v IT="$IT" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    ts = (TS - 56.5) / 8.5;
    tr = (TR - 12) / 6;
    pi = (PI - 0.5) / 0.5;
    rt = (RT - 0.5) / 0.5;
    it = (IT - 12.5) / 7.5;
    kwh = 350 + 40*ts - 30*tr - 15*pi - 20*rt - 25*it + 10*ts*it;
    avail = 85 + 5*ts + 2*tr + 1*pi + 3*rt + 3*it + 1.5*ts*tr;
    if (kwh < 150) kwh = 150;
    if (avail < 60) avail = 60; if (avail > 100) avail = 100;
    printf "{\"monthly_kwh\": %.0f, \"availability_pct\": %.0f}", kwh + n1*12, avail + n2*2;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

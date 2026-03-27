#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: LoRaWAN Parameters
set -euo pipefail

OUTFILE=""
SF=""
TP=""
CR=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --spreading_factor) SF="$2"; shift 2 ;;
        --tx_power_dbm) TP="$2"; shift 2 ;;
        --coding_rate) CR="$2"; shift 2 ;;
        *) shift ;;
    esac
done

if [[ -z "$OUTFILE" ]] || [ -z "$SF" ] || [ -z "$TP" ] || [ -z "$CR" ]; then
    echo "ERROR: missing required arguments" >&2
    exit 1
fi

RESULT=$(awk -v SF="$SF" -v TP="$TP" -v CR="$CR" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    sf = (SF - 9.5) / 2.5;
    tp = (TP - 11) / 9;
    cr = (CR - 6.5) / 1.5;
    rng = 5 + 3*sf + 2*tp + 0.8*cr + 0.5*sf*tp - 0.4*sf*sf + 0.3*tp*cr;
    bat = 365 - 80*sf - 60*tp - 20*cr + 15*sf*sf + 10*tp*tp - 5*sf*tp;
    if (rng < 0.5) rng = 0.5; if (bat < 10) bat = 10;
    printf "{\"range_km\": %.1f, \"battery_life_days\": %.0f}", rng + n1*0.5, bat + n2*20;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

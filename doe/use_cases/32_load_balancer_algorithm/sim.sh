#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Load Balancer Algorithm
set -euo pipefail

OUTFILE=""
ALG=""
HI=""
DT=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --algorithm) ALG="$2"; shift 2 ;;
        --health_interval) HI="$2"; shift 2 ;;
        --drain_timeout) DT="$2"; shift 2 ;;
        *) shift ;;
    esac
done

if [[ -z "$OUTFILE" ]] || [ -z "$ALG" ] || [ -z "$HI" ] || [ -z "$DT" ]; then
    echo "ERROR: missing required arguments" >&2
    exit 1
fi

RESULT=$(awk -v ALG="$ALG" -v HI="$HI" -v DT="$DT" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    if (ALG == "round_robin") a = 0; else if (ALG == "least_conn") a = 1; else a = -0.5;
    hi = (HI - 17.5) / 12.5;
    dt = (DT - 35) / 25;
    avail = 99.5 + 0.3*a - 0.15*hi + 0.1*dt + 0.05*a*dt;
    imb = 8 - 5*a + 2*hi - 1.5*dt + 1.2*a*hi;
    if (avail > 99.999) avail = 99.999; if (avail < 95) avail = 95;
    if (imb < 0.5) imb = 0.5;
    printf "{\"availability\": %.3f, \"imbalance_pct\": %.1f}", avail + n1*0.05, imb + n2*1.5;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

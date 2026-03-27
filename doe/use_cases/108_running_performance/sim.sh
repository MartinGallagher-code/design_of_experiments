#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Running Training Plan
set -euo pipefail

OUTFILE=""
WK=""
LR=""
IP=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --weekly_km) WK="$2"; shift 2 ;;
        --long_run_pct) LR="$2"; shift 2 ;;
        --interval_pct_max) IP="$2"; shift 2 ;;
        --rest_days) shift 2 ;;
        --runner_level) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$WK" ] || [ -z "$LR" ] || [ -z "$IP" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v WK="$WK" -v LR="$LR" -v IP="$IP" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    wk = (WK - 40) / 20;
    lr = (LR - 30) / 10;
    ip = (IP - 90) / 10;
    vo2 = 3.0 + 1.5*wk + 0.5*lr + 1.2*ip - 0.4*wk*wk - 0.3*lr*lr - 0.5*ip*ip + 0.3*wk*ip;
    inj = 15 + 8*wk + 3*lr + 5*ip + 2*wk*wk + 1.5*ip*ip + 2*wk*lr + 1.5*wk*ip;
    if (vo2 < 0.5) vo2 = 0.5;
    if (inj < 2) inj = 2; if (inj > 60) inj = 60;
    printf "{\"vo2max_gain\": %.1f, \"injury_risk\": %.0f}", vo2 + n1*0.3, inj + n2*2;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

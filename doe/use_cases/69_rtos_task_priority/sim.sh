#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: RTOS Task Priority
set -euo pipefail

OUTFILE=""
TPL=""
TR=""
SS=""
PT=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --task_priority_levels) TPL="$2"; shift 2 ;;
        --tick_rate_hz) TR="$2"; shift 2 ;;
        --stack_size_bytes) SS="$2"; shift 2 ;;
        --preemption_threshold) PT="$2"; shift 2 ;;
        *) shift ;;
    esac
done

if [[ -z "$OUTFILE" ]] || [ -z "$TPL" ] || [ -z "$TR" ] || [ -z "$SS" ] || [ -z "$PT" ]; then
    echo "ERROR: missing required arguments" >&2
    exit 1
fi

RESULT=$(awk -v TPL="$TPL" -v TR="$TR" -v SS="$SS" -v PT="$PT" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    tpl = (TPL - 10) / 6;
    tr = (TR - 550) / 450;
    ss = (SS - 2304) / 1792;
    pt = (PT - 4.5) / 3.5;
    lat = 50 - 10*tpl - 20*tr - 5*ss - 8*pt + 4*tpl*tpl + 6*tr*tr + 2*tpl*tr + 3*pt*pt;
    util = 65 + 8*tpl + 10*tr - 5*ss + 4*pt - 3*tpl*tpl - 4*tr*tr + 2*tpl*pt;
    if (lat < 1) lat = 1; if (util > 100) util = 100; if (util < 20) util = 20;
    printf "{\"worst_case_latency_us\": %.0f, \"cpu_utilization_pct\": %.1f}", lat + n1*5, util + n2*3;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

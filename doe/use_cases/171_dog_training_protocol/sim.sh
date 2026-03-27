#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Dog Training Effectiveness
set -euo pipefail

OUTFILE=""
SM=""
RR=""
PR=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --session_min) SM="$2"; shift 2 ;;
        --reward_ratio_pct) RR="$2"; shift 2 ;;
        --progression_rate) PR="$2"; shift 2 ;;
        --method) shift 2 ;;
        --breed) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$SM" ] || [ -z "$RR" ] || [ -z "$PR" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v SM="$SM" -v RR="$RR" -v PR="$PR" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    sm = (SM - 12.5) / 7.5; rr = (RR - 65) / 35; pr = (PR - 3) / 2;
    rel = 75 + 3*sm + 5*rr - 2*pr - 2*sm*sm - 3*rr*rr - 1*pr*pr + 1.5*sm*rr;
    sess = 12 - 1.5*sm - 2*rr + 1.5*pr + 0.5*sm*sm + 0.8*rr*rr + 0.5*sm*pr;
    if (rel < 30) rel = 30; if (rel > 100) rel = 100;
    if (sess < 3) sess = 3;
    printf "{\"reliability_pct\": %.0f, \"sessions_to_learn\": %.0f}", rel + n1*3, sess + n2*1;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

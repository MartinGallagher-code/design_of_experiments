#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Message Queue Consumer Tuning
set -euo pipefail

OUTFILE=""
FB=""
MPR=""
NC=""
ST=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --fetch_min_bytes) FB="$2"; shift 2 ;;
        --max_poll_records) MPR="$2"; shift 2 ;;
        --num_consumers) NC="$2"; shift 2 ;;
        --session_timeout) ST="$2"; shift 2 ;;
        *) shift ;;
    esac
done

if [[ -z "$OUTFILE" ]] || [ -z "$FB" ] || [ -z "$MPR" ] || [ -z "$NC" ] || [ -z "$ST" ]; then
    echo "ERROR: missing required arguments" >&2
    exit 1
fi

RESULT=$(awk -v FB="$FB" -v MPR="$MPR" -v NC="$NC" -v ST="$ST" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    fb = (FB - 524288) / 524288;
    mpr = (MPR - 2550) / 2450;
    nc = (NC - 6.5) / 5.5;
    st = (ST - 25500) / 19500;
    thr = 120 + 30*fb + 25*mpr + 40*nc - 5*st + 10*fb*mpr - 15*nc*nc - 8*fb*fb;
    lag = 50000 - 15000*fb - 10000*mpr - 20000*nc + 5000*st + 8000*nc*nc + 3000*fb*st;
    if (thr < 1) thr = 1; if (lag < 0) lag = 0;
    printf "{\"throughput_mbps\": %.1f, \"consumer_lag\": %.0f}", thr + n1*8, lag + n2*3000;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

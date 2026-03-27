#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: ETL Batch Size Tuning
set -euo pipefail

OUTFILE=""
BS=""
WT=""
CI=""
TM=""
BUF=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --batch_size) BS="$2"; shift 2 ;;
        --writer_threads) WT="$2"; shift 2 ;;
        --commit_interval) CI="$2"; shift 2 ;;
        --transform_mode) TM="$2"; shift 2 ;;
        --buffer_mb) BUF="$2"; shift 2 ;;
        *) shift ;;
    esac
done

if [[ -z "$OUTFILE" ]] || [ -z "$BS" ] || [ -z "$WT" ] || [ -z "$CI" ] || [ -z "$TM" ] || [ -z "$BUF" ]; then
    echo "ERROR: missing required arguments" >&2
    exit 1
fi

RESULT=$(awk -v BS="$BS" -v WT="$WT" -v CI="$CI" -v TM="$TM" -v BUF="$BUF" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    bs = (BS - 50500) / 49500;
    wt = (WT - 8.5) / 7.5;
    ci = (CI - 25500) / 24500;
    tm = (TM == "vectorized") ? 1 : -1;
    buf = (BUF - 288) / 224;
    rps = 50000 + 20000*bs + 15000*wt + 5000*ci + 12000*tm + 8000*buf - 5000*bs*bs - 3000*wt*wt + 4000*bs*wt;
    mem = 2.0 + 1.5*bs + 0.8*wt + 0.3*ci + 0.5*tm + 2.0*buf - 0.3*wt*buf;
    if (rps < 1000) rps = 1000; if (mem < 0.5) mem = 0.5;
    printf "{\"rows_per_sec\": %.0f, \"peak_memory_gb\": %.1f}", rps + n1*3000, mem + n2*0.3;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

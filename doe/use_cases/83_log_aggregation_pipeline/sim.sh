#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Log Aggregation Pipeline
set -euo pipefail

OUTFILE=""
BSZ=""
FI=""
PT=""
CR=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --batch_size_kb) BSZ="$2"; shift 2 ;;
        --flush_interval_sec) FI="$2"; shift 2 ;;
        --parser_threads) PT="$2"; shift 2 ;;
        --compression_ratio) CR="$2"; shift 2 ;;
        *) shift ;;
    esac
done

if [[ -z "$OUTFILE" ]] || [ -z "$BSZ" ] || [ -z "$FI" ] || [ -z "$PT" ] || [ -z "$CR" ]; then
    echo "ERROR: missing required arguments" >&2
    exit 1
fi

RESULT=$(awk -v BSZ="$BSZ" -v FI="$FI" -v PT="$PT" -v CR="$CR" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    bsz = (BSZ - 1056) / 992;
    fi = (FI - 15.5) / 14.5;
    pt = (PT - 8.5) / 7.5;
    cr = (CR - 5) / 4;
    ing = 2.5 + 1.0*bsz - 0.3*fi + 0.8*pt - 0.4*cr - 0.3*bsz*bsz + 0.2*bsz*pt - 0.15*cr*pt;
    qlat = 80 - 15*bsz + 20*fi - 10*pt + 8*cr + 5*bsz*bsz + 3*fi*fi - 4*pt*bsz;
    if (ing < 0.1) ing = 0.1; if (qlat < 5) qlat = 5;
    printf "{\"ingestion_rate_gbps\": %.2f, \"query_latency_ms\": %.0f}", ing + n1*0.15, qlat + n2*6;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

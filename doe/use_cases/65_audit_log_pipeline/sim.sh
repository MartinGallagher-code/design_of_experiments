#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Audit Log Pipeline
set -euo pipefail

OUTFILE=""
BS=""
FI=""
CL=""
BP=""
WT=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --batch_size) BS="$2"; shift 2 ;;
        --flush_interval_ms) FI="$2"; shift 2 ;;
        --compression_level) CL="$2"; shift 2 ;;
        --buffer_pool_mb) BP="$2"; shift 2 ;;
        --writer_threads) WT="$2"; shift 2 ;;
        *) shift ;;
    esac
done

if [[ -z "$OUTFILE" ]] || [ -z "$BS" ] || [ -z "$FI" ] || [ -z "$CL" ] || [ -z "$BP" ] || [ -z "$WT" ]; then
    echo "ERROR: missing required arguments" >&2
    exit 1
fi

RESULT=$(awk -v BS="$BS" -v FI="$FI" -v CL="$CL" -v BP="$BP" -v WT="$WT" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    bs = (BS - 5050) / 4950;
    fi = (FI - 2550) / 2450;
    cl = (CL - 5) / 4;
    bp = (BP - 272) / 240;
    wt = (WT - 4.5) / 3.5;
    rate = 50000 + 15000*bs - 5000*fi - 3000*cl + 10000*bp + 12000*wt - 4000*bs*bs + 3000*bs*wt - 2000*cl*wt;
    lat = 200 - 40*bs + 80*fi + 20*cl - 30*bp - 25*wt + 15*fi*fi + 10*bs*fi - 8*bp*wt;
    if (rate < 1000) rate = 1000; if (lat < 5) lat = 5;
    printf "{\"ingest_rate_eps\": %.0f, \"end_to_end_latency_ms\": %.0f}", rate + n1*3000, lat + n2*15;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

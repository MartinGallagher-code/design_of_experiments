#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Database Connection Pooling
set -euo pipefail

OUTFILE=""
PS=""
IT=""
ML=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --pool_size) PS="$2"; shift 2 ;;
        --idle_timeout) IT="$2"; shift 2 ;;
        --max_lifetime) ML="$2"; shift 2 ;;
        *) shift ;;
    esac
done

if [[ -z "$OUTFILE" ]] || [ -z "$PS" ] || [ -z "$IT" ] || [ -z "$ML" ]; then
    echo "ERROR: missing required arguments" >&2
    exit 1
fi

RESULT=$(awk -v PS="$PS" -v IT="$IT" -v ML="$ML" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    ps = (PS - 27.5) / 22.5;
    it = (IT - 165) / 135;
    ml = (ML - 1950) / 1650;
    thr = 5000 + 1500*ps - 300*it + 200*ml - 800*ps*ps - 200*it*it + 150*ps*it;
    lat = 12 - 4*ps + 2*it - 1*ml + 3*ps*ps + 1.5*it*it - 0.8*ps*ml;
    if (thr < 100) thr = 100; if (lat < 1) lat = 1;
    printf "{\"throughput_qps\": %.0f, \"p95_latency_ms\": %.1f}", thr + n1*200, lat + n2*1.5;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

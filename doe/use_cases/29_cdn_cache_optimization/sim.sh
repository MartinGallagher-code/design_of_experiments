#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: CDN Cache Hit Optimization
set -euo pipefail

OUTFILE=""
TTL=""
POL=""
SZ=""
PF=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --ttl_hours) TTL="$2"; shift 2 ;;
        --cache_policy) POL="$2"; shift 2 ;;
        --cache_size_gb) SZ="$2"; shift 2 ;;
        --prefetch) PF="$2"; shift 2 ;;
        *) shift ;;
    esac
done

if [[ -z "$OUTFILE" ]] || [ -z "$TTL" ] || [ -z "$POL" ] || [ -z "$SZ" ] || [ -z "$PF" ]; then
    echo "ERROR: missing required arguments" >&2
    exit 1
fi

RESULT=$(awk -v TTL="$TTL" -v POL="$POL" -v SZ="$SZ" -v PF="$PF" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    ttl = (TTL - 12.5) / 11.5;
    pol = (POL == "lfu") ? 1 : -1;
    sz = (SZ - 125) / 75;
    pf = (PF == "on") ? 1 : -1;
    hit = 72 + 8*ttl + 4*pol + 10*sz + 6*pf + 3*ttl*sz + 2*pol*pf - 1.5*ttl*ttl;
    bw = 15 - 4*ttl - 2*pol - 6*sz - 3*pf - 1.5*ttl*sz;
    if (hit > 99) hit = 99; if (hit < 30) hit = 30;
    if (bw < 0.5) bw = 0.5;
    printf "{\"hit_ratio\": %.1f, \"origin_bandwidth\": %.2f}", hit + n1*2, bw + n2*0.8;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

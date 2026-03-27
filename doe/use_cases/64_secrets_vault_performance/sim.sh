#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Secrets Vault Performance
set -euo pipefail

OUTFILE=""
SW=""
CSZ=""
LT=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --seal_wrap_threads) SW="$2"; shift 2 ;;
        --cache_size_mb) CSZ="$2"; shift 2 ;;
        --lease_ttl_sec) LT="$2"; shift 2 ;;
        *) shift ;;
    esac
done

if [[ -z "$OUTFILE" ]] || [ -z "$SW" ] || [ -z "$CSZ" ] || [ -z "$LT" ]; then
    echo "ERROR: missing required arguments" >&2
    exit 1
fi

RESULT=$(awk -v SW="$SW" -v CSZ="$CSZ" -v LT="$LT" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    sw = (SW - 4.5) / 3.5;
    csz = (CSZ - 288) / 224;
    lt = (LT - 315) / 285;
    lat = 15 - 4*sw - 6*csz + 2*lt + 2*sw*sw + 3*csz*csz + 1*lt*lt - 1.5*sw*csz;
    thr = 5000 + 1500*sw + 2000*csz - 500*lt - 600*sw*sw - 800*csz*csz + 400*sw*csz;
    if (lat < 0.5) lat = 0.5; if (thr < 100) thr = 100;
    printf "{\"read_latency_ms\": %.1f, \"throughput_ops\": %.0f}", lat + n1*1.5, thr + n2*300;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

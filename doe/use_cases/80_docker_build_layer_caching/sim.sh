#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Docker Build Layer Caching
set -euo pipefail

OUTFILE=""
BCM=""
ML=""
SQ=""
BAC=""
MS=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --build_cache_mode) BCM="$2"; shift 2 ;;
        --max_layers) ML="$2"; shift 2 ;;
        --squash_enabled) SQ="$2"; shift 2 ;;
        --build_arg_count) BAC="$2"; shift 2 ;;
        --multistage_stages) MS="$2"; shift 2 ;;
        *) shift ;;
    esac
done

if [[ -z "$OUTFILE" ]] || [ -z "$BCM" ] || [ -z "$ML" ] || [ -z "$SQ" ] || [ -z "$BAC" ] || [ -z "$MS" ]; then
    echo "ERROR: missing required arguments" >&2
    exit 1
fi

RESULT=$(awk -v BCM="$BCM" -v ML="$ML" -v SQ="$SQ" -v BAC="$BAC" -v MS="$MS" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    bcm = (BCM == "registry") ? 1 : -1;
    ml = (ML - 17.5) / 12.5;
    sq = (SQ == "on") ? 1 : -1;
    bac = (BAC - 5) / 5;
    ms = (MS - 3) / 2;
    bt = 120 - 20*bcm + 15*ml - 10*sq + 8*bac - 12*ms + 5*ml*ml + 3*bcm*ml - 4*sq*ms;
    isz = 450 + 30*bcm + 50*ml - 80*sq + 20*bac - 40*ms + 15*ml*ml - 10*sq*ml;
    if (bt < 5) bt = 5; if (isz < 20) isz = 20;
    printf "{\"build_time_sec\": %.0f, \"image_size_mb\": %.0f}", bt + n1*8, isz + n2*25;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Edge Inference Quantization
set -euo pipefail

OUTFILE=""
WB=""
AB=""
BS=""
NT=""
CK=""
MP=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --weight_bits) WB="$2"; shift 2 ;;
        --activation_bits) AB="$2"; shift 2 ;;
        --batch_size) BS="$2"; shift 2 ;;
        --num_threads) NT="$2"; shift 2 ;;
        --cache_size_kb) CK="$2"; shift 2 ;;
        --memory_pool_mb) MP="$2"; shift 2 ;;
        *) shift ;;
    esac
done

if [[ -z "$OUTFILE" ]] || [ -z "$WB" ] || [ -z "$AB" ] || [ -z "$BS" ] || [ -z "$NT" ]; then
    echo "ERROR: missing required arguments" >&2
    exit 1
fi

RESULT=$(awk -v WB="$WB" -v AB="$AB" -v BS="$BS" -v NT="$NT" -v CK="$CK" -v MP="$MP" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    wb = (WB - 10) / 6;
    ab = (AB - 10) / 6;
    bs = (BS - 16.5) / 15.5;
    nt = (NT - 2.5) / 1.5;
    ck = (CK - 288) / 224;
    mp = (MP - 72) / 56;
    lat = 25 - 5*wb - 4*ab + 8*bs - 6*nt - 3*ck - 2*mp + 2*wb*ab + 1.5*bs*nt;
    aloss = 5 - 3*wb - 2.5*ab + 0.3*bs - 0.1*nt - 0.2*ck + 0.1*mp + 1.5*wb*ab + 0.5*wb*wb;
    if (lat < 1) lat = 1; if (aloss < 0.1) aloss = 0.1;
    printf "{\"inference_latency_ms\": %.1f, \"accuracy_loss_pct\": %.2f}", lat + n1*2, aloss + n2*0.3;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

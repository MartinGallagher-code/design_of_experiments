#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: DNS Resolver Caching
set -euo pipefail

OUTFILE=""
CS=""
MT=""
PF=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --cache_size) CS="$2"; shift 2 ;;
        --min_ttl_s) MT="$2"; shift 2 ;;
        --prefetch_pct) PF="$2"; shift 2 ;;
        *) shift ;;
    esac
done

if [[ -z "$OUTFILE" ]] || [ -z "$CS" ] || [ -z "$MT" ] || [ -z "$PF" ]; then
    echo "ERROR: missing required arguments" >&2
    exit 1
fi

RESULT=$(awk -v CS="$CS" -v MT="$MT" -v PF="$PF" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    cs = (CS - 255000) / 245000;
    mt = (MT - 1815) / 1785;
    pf = (PF - 45) / 45;
    res = 25 - 8*cs - 6*mt - 10*pf + 3*cs*cs + 2*mt*mt + 4*pf*pf + 1.5*cs*mt;
    hit = 72 + 10*cs + 8*mt + 12*pf - 3*cs*cs - 2*mt*mt - 4*pf*pf + 2*cs*pf;
    if (res < 0.5) res = 0.5; if (hit > 99.5) hit = 99.5; if (hit < 20) hit = 20;
    printf "{\"avg_resolution_ms\": %.1f, \"cache_hit_rate\": %.1f}", res + n1*2, hit + n2*2;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

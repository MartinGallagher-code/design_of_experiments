#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Time-Series Downsampling
set -euo pipefail

OUTFILE=""
DI=""
RET=""
AF=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --downsample_interval_m) DI="$2"; shift 2 ;;
        --retention_days) RET="$2"; shift 2 ;;
        --agg_functions) AF="$2"; shift 2 ;;
        *) shift ;;
    esac
done

if [[ -z "$OUTFILE" ]] || [ -z "$DI" ] || [ -z "$RET" ] || [ -z "$AF" ]; then
    echo "ERROR: missing required arguments" >&2
    exit 1
fi

RESULT=$(awk -v DI="$DI" -v RET="$RET" -v AF="$AF" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    di = (DI - 30.5) / 29.5;
    ret = (RET - 186) / 179;
    af = (AF - 5) / 3;
    qp = 80 - 30*di + 40*ret - 20*af + 10*di*di + 15*ret*ret + 5*af*af + 8*di*ret;
    sg = 50 - 15*di + 35*ret + 5*af - 4*di*di + 8*ret*ret - 2*di*ret;
    if (qp < 5) qp = 5; if (sg < 1) sg = 1;
    printf "{\"query_p95_ms\": %.0f, \"storage_gb\": %.0f}", qp + n1*8, sg + n2*5;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

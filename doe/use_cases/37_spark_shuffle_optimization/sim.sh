#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Spark Shuffle Optimization
set -euo pipefail

OUTFILE=""
SP=""
SB=""
CC=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --shuffle_partitions) SP="$2"; shift 2 ;;
        --shuffle_buffer_kb) SB="$2"; shift 2 ;;
        --compress_codec) CC="$2"; shift 2 ;;
        *) shift ;;
    esac
done

if [[ -z "$OUTFILE" ]] || [ -z "$SP" ] || [ -z "$SB" ] || [ -z "$CC" ]; then
    echo "ERROR: missing required arguments" >&2
    exit 1
fi

RESULT=$(awk -v SP="$SP" -v SB="$SB" -v CC="$CC" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    sp = (SP - 275) / 225;
    sb = (SB - 144) / 112;
    cc = (CC == "zstd") ? 1 : -1;
    jt = 25 - 5*sp + 3*sb - 2*cc + 4*sp*sp + 2*sb*sb - 1.5*sp*sb + 0.8*sp*cc;
    spill = 15 - 4*sp - 6*sb - 3*cc + 3*sp*sp + 2*sb*sb + 1*sp*sb;
    if (jt < 2) jt = 2; if (spill < 0) spill = 0;
    printf "{\"job_time_min\": %.1f, \"shuffle_spill_gb\": %.1f}", jt + n1*1.5, spill + n2*1.2;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

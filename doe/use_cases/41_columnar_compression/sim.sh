#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Columnar Compression
set -euo pipefail

OUTFILE=""
CO=""
DI=""
PS=""
RG=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --codec) CO="$2"; shift 2 ;;
        --dictionary) DI="$2"; shift 2 ;;
        --page_size_kb) PS="$2"; shift 2 ;;
        --row_group_mb) RG="$2"; shift 2 ;;
        *) shift ;;
    esac
done

if [[ -z "$OUTFILE" ]] || [ -z "$CO" ] || [ -z "$DI" ] || [ -z "$PS" ] || [ -z "$RG" ]; then
    echo "ERROR: missing required arguments" >&2
    exit 1
fi

RESULT=$(awk -v CO="$CO" -v DI="$DI" -v PS="$PS" -v RG="$RG" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    co = (CO == "zstd") ? 1 : -1;
    di = (DI == "on") ? 1 : -1;
    ps = (PS - 544) / 480;
    rg = (RG - 144) / 112;
    ratio = 4.5 + 1.5*co + 1.2*di + 0.3*ps + 0.5*rg + 0.4*co*di + 0.2*di*ps;
    speed = 800 - 200*co + 100*di + 50*ps + 80*rg - 60*co*di + 30*ps*rg;
    if (ratio < 1) ratio = 1; if (speed < 100) speed = 100;
    printf "{\"compression_ratio\": %.2f, \"read_speed_mbps\": %.0f}", ratio + n1*0.3, speed + n2*40;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Data Lake Partitioning
set -euo pipefail

OUTFILE=""
PC=""
FF=""
TF=""
ZO=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --partition_cols) PC="$2"; shift 2 ;;
        --file_format) FF="$2"; shift 2 ;;
        --target_file_mb) TF="$2"; shift 2 ;;
        --z_order) ZO="$2"; shift 2 ;;
        *) shift ;;
    esac
done

if [[ -z "$OUTFILE" ]] || [ -z "$PC" ] || [ -z "$FF" ] || [ -z "$TF" ] || [ -z "$ZO" ]; then
    echo "ERROR: missing required arguments" >&2
    exit 1
fi

RESULT=$(awk -v PC="$PC" -v FF="$FF" -v TF="$TF" -v ZO="$ZO" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    if (PC == "date") pc = -1; else if (PC == "date_hour") pc = 0; else pc = 1;
    ff = (FF == "parquet") ? 1 : -1;
    tf = (TF - 160) / 96;
    zo = (ZO == "on") ? 1 : -1;
    qt = 12 - 3*pc + 1.5*ff - 2*tf - 4*zo + 1*pc*zo + 0.5*pc*pc;
    stc = 250 + 30*pc - 10*ff - 15*tf + 5*zo + 8*pc*tf;
    if (qt < 0.5) qt = 0.5; if (stc < 50) stc = 50;
    printf "{\"query_time_s\": %.1f, \"storage_cost_month\": %.0f}", qt + n1*1.5, stc + n2*20;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

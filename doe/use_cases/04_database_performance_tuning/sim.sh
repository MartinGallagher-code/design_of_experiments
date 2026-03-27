#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated PostgreSQL benchmark — accepts --<factor> <value> arguments.
#
# Model (hidden):
#   throughput ~ 5000 + 800*(sb_c) + 400*(wm_c) - 300*(mc_c) + 600*(ec_c) - 200*(wal_c) + 150*(ct_c) + noise
#   p99_latency ~ 12 - 2*(sb_c) - 1*(wm_c) + 3*(mc_c) - 1.5*(ec_c) + 1*(wal_c) + noise

set -euo pipefail

OUTFILE=""
SB="" WM="" MC="" EC="" WAL="" CT=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out)                OUTFILE="$2"; shift 2 ;;
        --shared_buffers)     SB="$2";      shift 2 ;;
        --work_mem)           WM="$2";      shift 2 ;;
        --max_connections)    MC="$2";      shift 2 ;;
        --effective_cache)    EC="$2";      shift 2 ;;
        --wal_level)          WAL="$2";     shift 2 ;;
        --checkpoint_timeout) CT="$2";      shift 2 ;;
        --pg_version|--storage) shift 2 ;;
        *)                    shift ;;
    esac
done

if [[ -z "$OUTFILE" ]]; then
    echo "Error: --out <path> is required" >&2
    exit 1
fi

RESULT=$(awk -v sb="$SB" -v wm="$WM" -v mc="$MC" -v ec="$EC" -v wal="$WAL" -v ct="$CT" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 500;
    n2 = (rand() - 0.5) * 2;

    sb_c = (sb+0 >= 640) ? 1 : -1;
    wm_c = (wm+0 >= 34) ? 1 : -1;
    mc_c = (mc+0 >= 125) ? 1 : -1;
    ec_c = (ec+0 >= 2304) ? 1 : -1;
    wal_c = (wal == "replica") ? 1 : -1;
    ct_c = (ct+0 >= 480) ? 1 : -1;

    tp = 5000 + 800*sb_c + 400*wm_c - 300*mc_c + 600*ec_c - 200*wal_c + 150*ct_c + n1;
    if (tp < 500) tp = 500;

    lat = 12 - 2*sb_c - 1*wm_c + 3*mc_c - 1.5*ec_c + 1*wal_c + n2;
    if (lat < 1) lat = 1;

    printf "{\"throughput\": %.0f, \"p99_latency\": %.2f}", tp, lat;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

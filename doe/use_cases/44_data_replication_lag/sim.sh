#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Data Replication Lag
set -euo pipefail

OUTFILE=""
SM=""
BB=""
PW=""
NB=""
COMP=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --sync_mode) SM="$2"; shift 2 ;;
        --binlog_batch_size) BB="$2"; shift 2 ;;
        --parallel_workers) PW="$2"; shift 2 ;;
        --network_buffer_kb) NB="$2"; shift 2 ;;
        --compression) COMP="$2"; shift 2 ;;
        *) shift ;;
    esac
done

if [[ -z "$OUTFILE" ]] || [ -z "$SM" ] || [ -z "$BB" ] || [ -z "$PW" ] || [ -z "$NB" ] || [ -z "$COMP" ]; then
    echo "ERROR: missing required arguments" >&2
    exit 1
fi

RESULT=$(awk -v SM="$SM" -v BB="$BB" -v PW="$PW" -v NB="$NB" -v COMP="$COMP" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    sm = (SM == "semi_sync") ? 1 : -1;
    bb = (BB - 50.5) / 49.5;
    pw = (PW - 8.5) / 7.5;
    nb = (NB - 544) / 480;
    comp = (COMP == "on") ? 1 : -1;
    lag = 200 + 150*sm - 80*bb - 100*pw - 40*nb - 30*comp + 50*sm*bb + 30*pw*nb;
    ready = 92 - 4*sm + 3*bb + 5*pw + 2*nb + 2*comp - 2*sm*pw;
    if (lag < 1) lag = 1; if (ready > 100) ready = 100; if (ready < 50) ready = 50;
    printf "{\"replication_lag_ms\": %.0f, \"failover_ready_pct\": %.1f}", lag + n1*30, ready + n2*1.5;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: HTTP/2 Stream Multiplexing
set -euo pipefail

OUTFILE=""
MCS=""
WS=""
HT=""
PR=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --max_concurrent_streams) MCS="$2"; shift 2 ;;
        --window_size_kb) WS="$2"; shift 2 ;;
        --header_table_kb) HT="$2"; shift 2 ;;
        --priority_enabled) PR="$2"; shift 2 ;;
        *) shift ;;
    esac
done

if [[ -z "$OUTFILE" ]] || [ -z "$MCS" ] || [ -z "$WS" ] || [ -z "$HT" ] || [ -z "$PR" ]; then
    echo "ERROR: missing required arguments" >&2
    exit 1
fi

RESULT=$(awk -v MCS="$MCS" -v WS="$WS" -v HT="$HT" -v PR="$PR" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    mcs = (MCS - 150) / 100;
    ws = (WS - 544) / 480;
    ht = (HT - 34) / 30;
    pr = (PR == "on") ? 1 : -1;
    plt = 1200 - 150*mcs - 200*ws - 80*ht - 100*pr + 40*mcs*mcs + 30*ws*ws + 20*mcs*ws;
    ttfb = 120 - 15*mcs - 30*ws - 10*ht - 20*pr + 5*mcs*ws + 8*ws*ws;
    if (plt < 200) plt = 200; if (ttfb < 20) ttfb = 20;
    printf "{\"page_load_ms\": %.0f, \"ttfb_ms\": %.0f}", plt + n1*60, ttfb + n2*10;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

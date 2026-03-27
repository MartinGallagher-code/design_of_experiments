#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Test Suite Sharding
set -euo pipefail

OUTFILE=""
SC=""
RFC=""
TM=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --shard_count) SC="$2"; shift 2 ;;
        --retry_flaky_count) RFC="$2"; shift 2 ;;
        --timeout_multiplier) TM="$2"; shift 2 ;;
        *) shift ;;
    esac
done

if [[ -z "$OUTFILE" ]] || [ -z "$SC" ] || [ -z "$RFC" ] || [ -z "$TM" ]; then
    echo "ERROR: missing required arguments" >&2
    exit 1
fi

RESULT=$(awk -v SC="$SC" -v RFC="$RFC" -v TM="$TM" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    sc = (SC - 9) / 7;
    rfc = (RFC - 1.5) / 1.5;
    tm = (TM - 2) / 1;
    wt = 30 - 12*sc + 3*rfc + 2*tm + 5*sc*sc + 1*rfc*rfc - 1.5*sc*rfc + 0.8*rfc*tm;
    flaky = 5 - 0.5*sc - 3*rfc + 1*tm + 0.3*sc*sc + 1*rfc*rfc - 0.5*rfc*tm;
    if (wt < 2) wt = 2; if (flaky < 0.1) flaky = 0.1;
    printf "{\"total_wall_time_min\": %.1f, \"flaky_failure_rate\": %.2f}", wt + n1*1.5, flaky + n2*0.5;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

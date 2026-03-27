#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Microservice Circuit Breaker
set -euo pipefail

OUTFILE=""
FT=""
TO=""
RI=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --failure_threshold) FT="$2"; shift 2 ;;
        --timeout_ms) TO="$2"; shift 2 ;;
        --reset_interval) RI="$2"; shift 2 ;;
        *) shift ;;
    esac
done

if [[ -z "$OUTFILE" ]] || [ -z "$FT" ] || [ -z "$TO" ] || [ -z "$RI" ]; then
    echo "ERROR: missing required arguments" >&2
    exit 1
fi

RESULT=$(awk -v FT="$FT" -v TO="$TO" -v RI="$RI" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    ft = (FT - 9) / 6;
    to = (TO - 2750) / 2250;
    ri = (RI - 32.5) / 27.5;
    err = 5.0 - 2.5*ft + 1.8*to - 1.2*ri + 1.5*ft*ft + 0.8*to*to + 0.6*ft*to;
    rec = 30 + 8*ft + 5*to + 12*ri - 3*ft*ri + 2*to*ri + 1.5*ri*ri;
    if (err < 0.1) err = 0.1; if (rec < 2) rec = 2;
    printf "{\"error_rate\": %.2f, \"recovery_time\": %.1f}", err + n1*0.5, rec + n2*2;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

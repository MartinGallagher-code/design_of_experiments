#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Certificate Rotation Strategy
set -euo pipefail

OUTFILE=""
CL=""
RW=""
SC=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --cert_lifetime_days) CL="$2"; shift 2 ;;
        --renewal_window_pct) RW="$2"; shift 2 ;;
        --stapling_cache_sec) SC="$2"; shift 2 ;;
        *) shift ;;
    esac
done

if [[ -z "$OUTFILE" ]] || [ -z "$CL" ] || [ -z "$RW" ] || [ -z "$SC" ]; then
    echo "ERROR: missing required arguments" >&2
    exit 1
fi

RESULT=$(awk -v CL="$CL" -v RW="$RW" -v SC="$SC" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    cl = (CL - 60) / 30;
    rw = (RW - 20) / 10;
    sc = (SC - 1950) / 1650;
    suc = 96 + 2*cl + 3*rw + 1*sc - 0.8*cl*cl - 0.5*rw*rw + 0.5*cl*rw;
    dt = 5 - 1.5*cl - 2*rw - 0.8*sc + 0.6*cl*cl + 0.4*rw*rw + 0.3*cl*rw;
    if (suc > 100) suc = 100; if (suc < 80) suc = 80;
    if (dt < 0) dt = 0;
    printf "{\"rotation_success_rate\": %.2f, \"downtime_sec\": %.1f}", suc + n1*0.5, dt + n2*0.8;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

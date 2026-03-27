#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Container Resource Limits
set -euo pipefail

OUTFILE=""
CR=""
CL=""
MR=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --cpu_request_m) CR="$2"; shift 2 ;;
        --cpu_limit_m) CL="$2"; shift 2 ;;
        --memory_request_mb) MR="$2"; shift 2 ;;
        *) shift ;;
    esac
done

if [[ -z "$OUTFILE" ]] || [ -z "$CR" ] || [ -z "$CL" ] || [ -z "$MR" ]; then
    echo "ERROR: missing required arguments" >&2
    exit 1
fi

RESULT=$(awk -v CR="$CR" -v CL="$CL" -v MR="$MR" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    cr = (CR - 550) / 450;
    cl = (CL - 1250) / 750;
    mr = (MR - 576) / 448;
    util = 65 + 15*cr - 8*cl + 10*mr - 6*cr*cr - 4*cl*cl + 3*cr*cl + 2*mr*cr;
    oom = 5 - 2*cr - 1.5*cl - 3*mr + 2*cr*cr + 1*cl*cl + 0.8*mr*mr + 0.5*cr*cl;
    if (util > 100) util = 100; if (util < 5) util = 5;
    if (oom < 0) oom = 0;
    printf "{\"utilization_pct\": %.1f, \"oom_kills_per_day\": %.1f}", util + n1*3, oom + n2*0.8;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

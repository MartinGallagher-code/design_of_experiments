#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Terraform Plan Optimization
set -euo pipefail

OUTFILE=""
PAR=""
REF=""
SLT=""
PC=""
POF=""
DEC=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --parallelism) PAR="$2"; shift 2 ;;
        --refresh_enabled) REF="$2"; shift 2 ;;
        --state_lock_timeout) SLT="$2"; shift 2 ;;
        --provider_cache) PC="$2"; shift 2 ;;
        --plan_out_format) POF="$2"; shift 2 ;;
        --detailed_exitcode) DEC="$2"; shift 2 ;;
        *) shift ;;
    esac
done

if [[ -z "$OUTFILE" ]] || [ -z "$PAR" ] || [ -z "$REF" ] || [ -z "$SLT" ] || [ -z "$PC" ]; then
    echo "ERROR: missing required arguments" >&2
    exit 1
fi

RESULT=$(awk -v PAR="$PAR" -v REF="$REF" -v SLT="$SLT" -v PC="$PC" -v POF="$POF" -v DEC="$DEC" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    par = (PAR - 10.5) / 9.5;
    ref = (REF == "on") ? 1 : -1;
    slt = (SLT - 62.5) / 57.5;
    pc = (PC == "on") ? 1 : -1;
    pof = (POF == "json") ? 1 : -1;
    dec = (DEC == "on") ? 1 : -1;
    pt = 45 - 12*par + 8*ref + 2*slt - 5*pc + 1*pof + 0.5*dec + 3*par*par - 2*par*pc;
    drift = 5 + 0.5*par + 4*ref + 0.3*slt + 0.2*pc + 0.1*pof + 0.3*dec + 0.5*ref*dec;
    if (pt < 3) pt = 3; if (drift < 0) drift = 0;
    printf "{\"plan_time_sec\": %.1f, \"state_drift_detected\": %.0f}", pt + n1*3, drift + n2*1;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

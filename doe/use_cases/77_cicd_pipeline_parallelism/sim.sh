#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: CI/CD Pipeline Parallelism
set -euo pipefail

OUTFILE=""
PJ=""
RC=""
CS=""
AC=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --parallel_jobs) PJ="$2"; shift 2 ;;
        --runner_cpu_cores) RC="$2"; shift 2 ;;
        --cache_strategy) CS="$2"; shift 2 ;;
        --artifact_compression) AC="$2"; shift 2 ;;
        *) shift ;;
    esac
done

if [[ -z "$OUTFILE" ]] || [ -z "$PJ" ] || [ -z "$RC" ] || [ -z "$CS" ] || [ -z "$AC" ]; then
    echo "ERROR: missing required arguments" >&2
    exit 1
fi

RESULT=$(awk -v PJ="$PJ" -v RC="$RC" -v CS="$CS" -v AC="$AC" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    pj = (PJ - 4.5) / 3.5;
    rc = (RC - 5) / 3;
    cs = (CS == "aggressive") ? 1 : -1;
    ac = (AC == "on") ? 1 : -1;
    dur = 25 - 8*pj - 5*rc - 6*cs - 2*ac + 3*pj*pj + 2*rc*rc - 2*pj*cs + 1*rc*ac;
    cost = 1.5 + 0.8*pj + 1.2*rc + 0.3*cs + 0.1*ac + 0.4*pj*rc - 0.2*cs*ac;
    if (dur < 2) dur = 2; if (cost < 0.1) cost = 0.1;
    printf "{\"pipeline_duration_min\": %.1f, \"resource_cost_usd\": %.2f}", dur + n1*2, cost + n2*0.15;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

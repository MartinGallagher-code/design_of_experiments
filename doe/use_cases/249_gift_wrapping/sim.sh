#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Gift Wrapping Efficiency
set -euo pipefail

OUTFILE=""
OH=""
TS=""
RC=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --overhang_cm) OH="$2"; shift 2 ;;
        --tape_strips) TS="$2"; shift 2 ;;
        --ribbon_curls) RC="$2"; shift 2 ;;
        --paper_type) shift 2 ;;
        --box_size) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$OH" ] || [ -z "$TS" ] || [ -z "$RC" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v OH="$OH" -v TS="$TS" -v RC="$RC" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    oh = (OH - 5) / 3; ts = (TS - 5.5) / 2.5; rc = (RC - 3) / 3;
    pres = 6.0 + 0.5*oh + 0.3*ts + 1.0*rc - 0.5*oh*oh - 0.2*ts*ts - 0.3*rc*rc + 0.2*oh*rc;
    waste = 10 + 5*oh + 0.5*ts + 1*rc + 1*oh*oh;
    if (pres < 1) pres = 1; if (pres > 10) pres = 10; if (waste < 2) waste = 2;
    printf "{\"presentation\": %.1f, \"waste_pct\": %.0f}", pres + n1*0.3, waste + n2*1;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

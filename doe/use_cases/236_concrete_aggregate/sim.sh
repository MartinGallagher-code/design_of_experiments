#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Aggregate Gradation Optimization
set -euo pipefail

OUTFILE=""
CA=""
FM=""
MS=""
FN=""
AN=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --coarse_pct) CA="$2"; shift 2 ;;
        --fineness_mod) FM="$2"; shift 2 ;;
        --max_size_mm) MS="$2"; shift 2 ;;
        --fines_pct) FN="$2"; shift 2 ;;
        --angularity) AN="$2"; shift 2 ;;
        --cement) shift 2 ;;
        --target_slump) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$CA" ] || [ -z "$FM" ] || [ -z "$MS" ] || [ -z "$FN" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v CA="$CA" -v FM="$FM" -v MS="$MS" -v FN="$FN" -v AN="$AN" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    ca = (CA - 62.5) / 12.5; fm = (FM - 2.7) / 0.4; ms = (MS - 17.5) / 7.5; fn = (FN - 2.5) / 2.5; an = (AN - 3) / 2;
    work = 6.0 - 0.5*ca + 0.3*fm + 0.5*ms + 0.2*fn - 0.8*an + 0.2*ca*fm;
    str_ = 30 + 2*ca + 1*fm - 1*ms - 1*fn + 2*an + 0.5*ca*an;
    if (work < 1) work = 1; if (work > 10) work = 10; if (str_ < 15) str_ = 15;
    printf "{\"workability_score\": %.1f, \"strength_28d_mpa\": %.0f}", work + n1*0.3, str_ + n2*1.5;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

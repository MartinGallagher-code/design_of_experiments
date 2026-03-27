#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Dog Kibble Formulation
set -euo pipefail

OUTFILE=""
PR=""
FT=""
FB=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --protein_pct) PR="$2"; shift 2 ;;
        --fat_pct) FT="$2"; shift 2 ;;
        --fiber_pct) FB="$2"; shift 2 ;;
        --breed_size) shift 2 ;;
        --life_stage) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$PR" ] || [ -z "$FT" ] || [ -z "$FB" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v PR="$PR" -v FT="$FT" -v FB="$FB" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    pr = (PR - 27.5) / 7.5; ft = (FT - 13) / 5; fb = (FB - 4) / 2;
    pal = 6.5 + 0.5*pr + 1.2*ft - 0.4*fb - 0.3*pr*pr - 0.4*ft*ft + 0.2*pr*ft;
    coat = 6.0 + 0.8*pr + 0.6*ft + 0.2*fb - 0.3*pr*pr - 0.2*ft*ft + 0.15*pr*fb;
    if (pal < 1) pal = 1; if (pal > 10) pal = 10;
    if (coat < 1) coat = 1; if (coat > 10) coat = 10;
    printf "{\"palatability\": %.1f, \"coat_score\": %.1f}", pal + n1*0.3, coat + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

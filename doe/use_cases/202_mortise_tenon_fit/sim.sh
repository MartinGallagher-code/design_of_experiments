#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Mortise & Tenon Fit
set -euo pipefail

OUTFILE=""
TL=""
SD=""
GV=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --tolerance_mm) TL="$2"; shift 2 ;;
        --shoulder_mm) SD="$2"; shift 2 ;;
        --glue_viscosity) GV="$2"; shift 2 ;;
        --joint_type) shift 2 ;;
        --wood) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$TL" ] || [ -z "$SD" ] || [ -z "$GV" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v TL="$TL" -v SD="$SD" -v GV="$GV" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    tl = (TL - 0.275) / 0.225; sd = (SD - 6.5) / 3.5; gv = (GV - 4500) / 3500;
    pull = 3.5 - 0.8*tl + 0.6*sd + 0.3*gv + 0.5*tl*tl - 0.2*sd*sd + 0.2*tl*gv;
    asm_ = 6.0 + 1.2*tl - 0.3*sd - 0.5*gv - 0.3*tl*tl + 0.2*sd*sd + 0.2*tl*sd;
    if (pull < 0.5) pull = 0.5; if (asm_ < 1) asm_ = 1; if (asm_ > 10) asm_ = 10;
    printf "{\"pull_strength_kn\": %.2f, \"assembly_score\": %.1f}", pull + n1*0.2, asm_ + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

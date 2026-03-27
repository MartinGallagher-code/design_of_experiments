#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Oil Paint Drying Medium
set -euo pipefail
OUTFILE=""
LO=""
MP=""
TH=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --linseed_pct) LO="$2"; shift 2 ;;
        --medium_pct) MP="$2"; shift 2 ;;
        --thickness_mm) TH="$2"; shift 2 ;;
        --pigment) shift 2 ;;
        --support) shift 2 ;;
        *) shift ;;
    esac
done
if [ -z "$LO" ] || [ -z "$MP" ] || [ -z "$TH" ]; then
    echo "Missing required factors" >&2; exit 1
fi
RESULT=$(awk -v LO="$LO" -v MP="$MP" -v TH="$TH" -v seed="$RANDOM" '
BEGIN {
    srand(seed); n1=(rand()-0.5)*2; n2=(rand()-0.5)*2;
    lo=(LO-30)/20;mp=(MP-15)/10;th=(TH-1.75)/1.25;
    gloss=6+0.8*lo+0.5*mp-0.3*th-0.3*lo*lo-0.2*mp*mp+0.2*lo*mp;
    yel=3+1.5*lo+0.3*mp+0.5*th+0.5*lo*lo+0.2*th*th+0.3*lo*th;
    if(gloss<1)gloss=1;if(gloss>10)gloss=10;if(yel<0.5)yel=0.5;
    printf "{\"gloss_score\": %.1f, \"yellowing_de\": %.1f}",gloss+n1*0.3,yel+n2*0.3;
}')
mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

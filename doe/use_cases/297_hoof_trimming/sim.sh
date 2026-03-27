#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Hoof Trimming Schedule
set -euo pipefail
OUTFILE=""
TW=""
HH=""
TA=""
BP=""
EX=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --trim_weeks) TW="$2"; shift 2 ;;
        --heel_height_mm) HH="$2"; shift 2 ;;
        --toe_angle_deg) TA="$2"; shift 2 ;;
        --balance_pct) BP="$2"; shift 2 ;;
        --exercise_hrs) EX="$2"; shift 2 ;;
        --animal) shift 2 ;;
        --surface) shift 2 ;;
        *) shift ;;
    esac
done
if [ -z "$TW" ] || [ -z "$HH" ] || [ -z "$TA" ] || [ -z "$BP" ]; then
    echo "Missing required factors" >&2; exit 1
fi
RESULT=$(awk -v TW="$TW" -v HH="$HH" -v TA="$TA" -v BP="$BP" -v EX="$EX" -v seed="$RANDOM" '
BEGIN {
    srand(seed); n1=(rand()-0.5)*2; n2=(rand()-0.5)*2;
    tw=(TW-11)/5;hh=(HH-30)/10;ta=(TA-50)/5;bp=(BP-50)/5;ex=(EX-5)/3;
    lame=2.5+0.5*tw-0.3*hh+0.2*ta+0.2*bp-0.3*ex+0.2*tw*tw+0.1*tw*hh;
    hf=6-0.5*tw+0.3*hh+0.2*ta-0.1*bp+0.4*ex+0.1*hh*ex;
    if(lame<1)lame=1;if(lame>5)lame=5;if(hf<1)hf=1;if(hf>10)hf=10;
    printf "{\"lameness_score\": %.1f, \"hoof_health\": %.1f}",lame+n1*0.15,hf+n2*0.3;
}')
mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

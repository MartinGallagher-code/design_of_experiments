#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Parachute Deployment Dynamics
set -euo pipefail
OUTFILE=""
DA=""
RR=""
SL=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --deploy_alt_m) DA="$2"; shift 2 ;;
        --reefing_pct) RR="$2"; shift 2 ;;
        --slider_pct) SL="$2"; shift 2 ;;
        --canopy) shift 2 ;;
        --load) shift 2 ;;
        *) shift ;;
    esac
done
if [ -z "$DA" ] || [ -z "$RR" ] || [ -z "$SL" ]; then
    echo "Missing required factors" >&2; exit 1
fi
RESULT=$(awk -v DA="$DA" -v RR="$RR" -v SL="$SL" -v seed="$RANDOM" '
BEGIN {
    srand(seed); n1=(rand()-0.5)*2; n2=(rand()-0.5)*2;
    da=(DA-900)/600;rr=(RR-25)/25;sl=(SL-80)/20;
    rel=95+2*da-1*rr+1*sl-1.5*da*da+0.5*rr*rr-0.5*sl*sl+0.5*da*sl;
    shk=3-0.3*da-1*rr-0.5*sl+0.3*da*da+0.5*rr*rr+0.2*da*rr;
    if(rel<75)rel=75;if(rel>100)rel=100;if(shk<0.5)shk=0.5;
    printf "{\"reliability_pct\": %.1f, \"opening_shock_g\": %.1f}",rel+n1*1,shk+n2*0.2;
}')
mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

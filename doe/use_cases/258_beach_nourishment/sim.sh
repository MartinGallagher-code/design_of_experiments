#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Beach Nourishment Longevity
set -euo pipefail
OUTFILE=""
GN=""
BW=""
DH=""
GS=""
VL=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --grain_mm) GN="$2"; shift 2 ;;
        --berm_width_m) BW="$2"; shift 2 ;;
        --dune_height_m) DH="$2"; shift 2 ;;
        --groin_spacing_m) GS="$2"; shift 2 ;;
        --volume_m3_m) VL="$2"; shift 2 ;;
        --wave_climate) shift 2 ;;
        --longshore_drift) shift 2 ;;
        *) shift ;;
    esac
done
if [ -z "$GN" ] || [ -z "$BW" ] || [ -z "$DH" ] || [ -z "$GS" ]; then
    echo "Missing required factors" >&2; exit 1
fi
RESULT=$(awk -v GN="$GN" -v BW="$BW" -v DH="$DH" -v GS="$GS" -v VL="$VL" -v seed="$RANDOM" '
BEGIN {
    srand(seed); n1=(rand()-0.5)*2; n2=(rand()-0.5)*2;
    gn=(GN-0.65)/0.35;bw=(BW-40)/20;dh=(DH-3.5)/1.5;gs=(GS-250)/150;vl=(VL-65)/35;
    ret=5+1*gn+1.5*bw+1*dh-0.5*gs+2*vl+0.3*gn*bw+0.2*bw*vl;
    res=6+0.5*gn+0.8*bw+1.2*dh-0.3*gs+0.5*vl+0.2*dh*vl;
    if(ret<1)ret=1;if(res<1)res=1;if(res>10)res=10;
    printf "{\"retention_yrs\": %.1f, \"storm_resilience\": %.1f}",ret+n1*0.3,res+n2*0.3;
}')
mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

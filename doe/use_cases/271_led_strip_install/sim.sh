#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: LED Strip Installation
set -euo pipefail
OUTFILE=""
LD=""
PH=""
DF=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --leds_per_m) LD="$2"; shift 2 ;;
        --psu_headroom_pct) PH="$2"; shift 2 ;;
        --diffuser_mm) DF="$2"; shift 2 ;;
        --voltage) shift 2 ;;
        --color) shift 2 ;;
        *) shift ;;
    esac
done
if [ -z "$LD" ] || [ -z "$PH" ] || [ -z "$DF" ]; then
    echo "Missing required factors" >&2; exit 1
fi
RESULT=$(awk -v LD="$LD" -v PH="$PH" -v DF="$DF" -v seed="$RANDOM" '
BEGIN {
    srand(seed); n1=(rand()-0.5)*2; n2=(rand()-0.5)*2;
    ld=(LD-75)/45;ph=(PH-25)/15;df=(DF-17.5)/12.5;
    unif=80+8*ld+3*ph+5*df-3*ld*ld-1*ph*ph-2*df*df+1*ld*df;
    hot=35+8*ld-3*ph-2*df+2*ld*ld+1*ph*ph+1*ld*ph;
    if(unif<50)unif=50;if(unif>100)unif=100;if(hot<15)hot=15;
    printf "{\"uniformity_pct\": %.0f, \"hotspot_temp_c\": %.0f}",unif+n1*2,hot+n2*2;
}')
mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

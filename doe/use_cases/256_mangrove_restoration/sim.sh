#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Mangrove Restoration Planting
set -euo pipefail
OUTFILE=""
DP=""
TZ=""
AM=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --density_per_m2) DP="$2"; shift 2 ;;
        --tidal_zone) TZ="$2"; shift 2 ;;
        --amendment_kg_m2) AM="$2"; shift 2 ;;
        --species) shift 2 ;;
        --site) shift 2 ;;
        *) shift ;;
    esac
done
if [ -z "$DP" ] || [ -z "$TZ" ] || [ -z "$AM" ]; then
    echo "Missing required factors" >&2; exit 1
fi
RESULT=$(awk -v DP="$DP" -v TZ="$TZ" -v AM="$AM" -v seed="$RANDOM" '
BEGIN {
    srand(seed); n1=(rand()-0.5)*2; n2=(rand()-0.5)*2;
    dp=(DP-3.5)/2.5;tz=(TZ-2)/1;am=(AM-1.5)/1.5;
    surv=65+5*dp-3*tz+8*am-3*dp*dp+2*tz*tz-2*am*am+2*dp*am;
    ht=25+3*dp-5*tz+6*am-1.5*dp*dp+1*tz*tz-2*am*am+1.5*tz*am;
    if(surv<20)surv=20;if(surv>98)surv=98;if(ht<5)ht=5;
    printf "{\"survival_1yr_pct\": %.0f, \"height_gain_cm\": %.0f}",surv+n1*3,ht+n2*2;
}')
mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

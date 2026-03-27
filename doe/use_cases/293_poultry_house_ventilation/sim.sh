#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Poultry House Ventilation
set -euo pipefail
OUTFILE=""
FR=""
IP=""
FI=""
LH=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --fan_rate_m3_s) FR="$2"; shift 2 ;;
        --inlet_pct) IP="$2"; shift 2 ;;
        --fog_interval_min) FI="$2"; shift 2 ;;
        --light_hrs) LH="$2"; shift 2 ;;
        --birds) shift 2 ;;
        --house_m2) shift 2 ;;
        *) shift ;;
    esac
done
if [ -z "$FR" ] || [ -z "$IP" ] || [ -z "$FI" ] || [ -z "$LH" ]; then
    echo "Missing required factors" >&2; exit 1
fi
RESULT=$(awk -v FR="$FR" -v IP="$IP" -v FI="$FI" -v LH="$LH" -v seed="$RANDOM" '
BEGIN {
    srand(seed); n1=(rand()-0.5)*2; n2=(rand()-0.5)*2;
    fr=(FR-5)/3;ip=(IP-50)/30;fi=(FI-17.5)/12.5;lh=(LH-19.5)/3.5;
    wg=55+5*fr+2*ip-3*fi+3*lh-2*fr*fr-1*ip*ip+1*fr*ip;
    mort=2-0.8*fr-0.3*ip+0.5*fi-0.2*lh+0.3*fr*fr+0.2*fi*fi+0.2*fi*lh;
    if(wg<30)wg=30;if(mort<0.1)mort=0.1;if(mort>8)mort=8;
    printf "{\"weight_gain_g_day\": %.0f, \"mortality_pct\": %.1f}",wg+n1*2,mort+n2*0.2;
}')
mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

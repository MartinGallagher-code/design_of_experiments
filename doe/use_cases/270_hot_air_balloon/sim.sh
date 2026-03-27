#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Hot Air Balloon Flight Planning
set -euo pipefail
OUTFILE=""
BB=""
EV=""
PS=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --burner_btu) BB="$2"; shift 2 ;;
        --envelope_m3) EV="$2"; shift 2 ;;
        --passengers) PS="$2"; shift 2 ;;
        --fuel_kg) shift 2 ;;
        --ambient_temp) shift 2 ;;
        *) shift ;;
    esac
done
if [ -z "$BB" ] || [ -z "$EV" ] || [ -z "$PS" ]; then
    echo "Missing required factors" >&2; exit 1
fi
RESULT=$(awk -v BB="$BB" -v EV="$EV" -v PS="$PS" -v seed="$RANDOM" '
BEGIN {
    srand(seed); n1=(rand()-0.5)*2; n2=(rand()-0.5)*2;
    bb=(BB-9000000)/3000000;ev=(EV-3000)/1000;ps=(PS-5)/3;
    flt=1.5+0.3*bb+0.5*ev-0.8*ps-0.2*bb*bb-0.1*ev*ev+0.1*bb*ev;
    ceil=500+100*bb+150*ev-120*ps-30*bb*bb-20*ev*ev+20*bb*ev;
    if(flt<0.3)flt=0.3;if(ceil<100)ceil=100;
    printf "{\"flight_hrs\": %.1f, \"ceiling_m\": %.0f}",flt+n1*0.1,ceil+n2*30;
}')
mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

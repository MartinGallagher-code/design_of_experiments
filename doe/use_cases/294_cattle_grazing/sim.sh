#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Rotational Grazing Pattern
set -euo pipefail
OUTFILE=""
RD=""
SD=""
GD=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --rest_days) RD="$2"; shift 2 ;;
        --stock_density_au_ha) SD="$2"; shift 2 ;;
        --graze_days) GD="$2"; shift 2 ;;
        --cattle) shift 2 ;;
        --paddock_count) shift 2 ;;
        *) shift ;;
    esac
done
if [ -z "$RD" ] || [ -z "$SD" ] || [ -z "$GD" ]; then
    echo "Missing required factors" >&2; exit 1
fi
RESULT=$(awk -v RD="$RD" -v SD="$SD" -v GD="$GD" -v seed="$RANDOM" '
BEGIN {
    srand(seed); n1=(rand()-0.5)*2; n2=(rand()-0.5)*2;
    rd=(RD-40.5)/19.5;sd=(SD-125)/75;gd=(GD-3)/2;
    rec=75+8*rd-5*sd-3*gd-3*rd*rd+2*sd*sd+1*gd*gd+2*rd*sd;
    adg=0.8+0.1*rd+0.05*sd-0.1*gd-0.05*rd*rd-0.03*sd*sd+0.02*rd*gd;
    if(rec<30)rec=30;if(rec>100)rec=100;if(adg<0.2)adg=0.2;
    printf "{\"pasture_recovery_pct\": %.0f, \"adg_kg\": %.2f}",rec+n1*3,adg+n2*0.05;
}')
mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

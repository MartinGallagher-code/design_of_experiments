#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: PCB Soldering Parameters
set -euo pipefail
OUTFILE=""
IT=""
CT=""
SD=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --iron_temp_c) IT="$2"; shift 2 ;;
        --contact_sec) CT="$2"; shift 2 ;;
        --solder_mm) SD="$2"; shift 2 ;;
        --flux) shift 2 ;;
        --tip) shift 2 ;;
        *) shift ;;
    esac
done
if [ -z "$IT" ] || [ -z "$CT" ] || [ -z "$SD" ]; then
    echo "Missing required factors" >&2; exit 1
fi
RESULT=$(awk -v IT="$IT" -v CT="$CT" -v SD="$SD" -v seed="$RANDOM" '
BEGIN {
    srand(seed); n1=(rand()-0.5)*2; n2=(rand()-0.5)*2;
    it=(IT-330)/50;ct=(CT-3)/2;sd=(SD-0.85)/0.35;
    jq=7+0.5*it+0.8*ct+0.3*sd-0.8*it*it-0.4*ct*ct-0.3*sd*sd+0.2*it*ct;
    br=3+0.3*it+0.5*ct+0.8*sd+0.2*it*it+0.3*ct*ct+0.3*ct*sd;
    if(jq<1)jq=1;if(jq>10)jq=10;if(br<0)br=0;
    printf "{\"joint_quality\": %.1f, \"bridge_rate\": %.1f}",jq+n1*0.3,br+n2*0.3;
}')
mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

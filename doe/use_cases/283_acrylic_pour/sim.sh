#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Acrylic Pour Technique
set -euo pipefail
OUTFILE=""
SD=""
CN=""
TA=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --silicone_drops) SD="$2"; shift 2 ;;
        --consistency) CN="$2"; shift 2 ;;
        --tilt_deg) TA="$2"; shift 2 ;;
        --medium) shift 2 ;;
        --base) shift 2 ;;
        *) shift ;;
    esac
done
if [ -z "$SD" ] || [ -z "$CN" ] || [ -z "$TA" ]; then
    echo "Missing required factors" >&2; exit 1
fi
RESULT=$(awk -v SD="$SD" -v CN="$CN" -v TA="$TA" -v seed="$RANDOM" '
BEGIN {
    srand(seed); n1=(rand()-0.5)*2; n2=(rand()-0.5)*2;
    sd=(SD-4.5)/3.5;cn=(CN-3)/2;ta=(TA-17.5)/12.5;
    cells=15+8*sd+3*cn+2*ta-2*sd*sd-1*cn*cn+1*sd*cn;
    sep=6+0.5*sd-0.3*cn+0.8*ta-0.3*sd*sd+0.2*cn*cn-0.2*ta*ta+0.2*cn*ta;
    if(cells<0)cells=0;if(sep<1)sep=1;if(sep>10)sep=10;
    printf "{\"cell_count\": %.0f, \"color_separation\": %.1f}",cells+n1*2,sep+n2*0.3;
}')
mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

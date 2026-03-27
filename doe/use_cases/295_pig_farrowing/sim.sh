#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Pig Farrowing Pen Design
set -euo pipefail
OUTFILE=""
CT=""
HM=""
SP=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --creep_temp_c) CT="$2"; shift 2 ;;
        --heat_mat_pct) HM="$2"; shift 2 ;;
        --space_m2) SP="$2"; shift 2 ;;
        --breed) shift 2 ;;
        --litter_size) shift 2 ;;
        *) shift ;;
    esac
done
if [ -z "$CT" ] || [ -z "$HM" ] || [ -z "$SP" ]; then
    echo "Missing required factors" >&2; exit 1
fi
RESULT=$(awk -v CT="$CT" -v HM="$HM" -v SP="$SP" -v seed="$RANDOM" '
BEGIN {
    srand(seed); n1=(rand()-0.5)*2; n2=(rand()-0.5)*2;
    ct=(CT-31.5)/3.5;hm=(HM-50)/50;sp=(SP-5.5)/1.5;
    surv=85+3*ct+4*hm+2*sp-3*ct*ct-1.5*hm*hm-1*sp*sp+1*ct*hm;
    comf=6+0.3*ct+0.5*hm+1.2*sp-0.5*ct*ct-0.2*hm*hm-0.3*sp*sp+0.2*hm*sp;
    if(surv<60)surv=60;if(surv>98)surv=98;if(comf<1)comf=1;if(comf>10)comf=10;
    printf "{\"piglet_survival_pct\": %.0f, \"sow_comfort\": %.1f}",surv+n1*2,comf+n2*0.3;
}')
mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

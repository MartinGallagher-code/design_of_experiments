#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Fish Farm Stocking Density
set -euo pipefail
OUTFILE=""
DK=""
FP=""
EX=""
AE=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --density_kg_m3) DK="$2"; shift 2 ;;
        --feed_pct_bw) FP="$2"; shift 2 ;;
        --exchange_pct) EX="$2"; shift 2 ;;
        --aeration) AE="$2"; shift 2 ;;
        --species) shift 2 ;;
        --cage) shift 2 ;;
        *) shift ;;
    esac
done
if [ -z "$DK" ] || [ -z "$FP" ] || [ -z "$EX" ] || [ -z "$AE" ]; then
    echo "Missing required factors" >&2; exit 1
fi
RESULT=$(awk -v DK="$DK" -v FP="$FP" -v EX="$EX" -v AE="$AE" -v seed="$RANDOM" '
BEGIN {
    srand(seed); n1=(rand()-0.5)*2; n2=(rand()-0.5)*2;
    dk=(DK-25)/15;fp=(FP-2.5)/1.5;ex=(EX-30)/20;ae=(AE=="high")?1:-1;
    gr=8+1*dk+2*fp+1*ex+0.5*ae-0.8*dk*dk-0.5*fp*fp+0.3*dk*fp;
    mort=3+1.5*dk+0.5*fp-1*ex-0.5*ae+0.5*dk*dk+0.3*dk*fp;
    if(gr<1)gr=1;if(mort<0.5)mort=0.5;if(mort>15)mort=15;
    printf "{\"growth_g_day\": %.1f, \"mortality_pct\": %.1f}",gr+n1*0.5,mort+n2*0.3;
}')
mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Wire Gauge & Run Length
set -euo pipefail
OUTFILE=""
AW=""
RL=""
FL=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --awg) AW="$2"; shift 2 ;;
        --run_m) RL="$2"; shift 2 ;;
        --fill_pct) FL="$2"; shift 2 ;;
        --circuit) shift 2 ;;
        --conductor) shift 2 ;;
        *) shift ;;
    esac
done
if [ -z "$AW" ] || [ -z "$RL" ] || [ -z "$FL" ]; then
    echo "Missing required factors" >&2; exit 1
fi
RESULT=$(awk -v AW="$AW" -v RL="$RL" -v FL="$FL" -v seed="$RANDOM" '
BEGIN {
    srand(seed); n1=(rand()-0.5)*2; n2=(rand()-0.5)*2;
    aw=(AW-14)/4;rl=(RL-17.5)/12.5;fl=(FL-40)/20;
    vd=3+1.5*aw+1.2*rl+0.3*fl+0.3*aw*aw+0.2*rl*rl+0.3*aw*rl;
    cost=2-0.8*aw+0.1*rl+0.05*fl+0.3*aw*aw;
    if(vd<0.5)vd=0.5;if(cost<0.5)cost=0.5;
    printf "{\"voltage_drop_pct\": %.1f, \"cost_per_m\": %.2f}",vd+n1*0.2,cost+n2*0.1;
}')
mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

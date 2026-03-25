#!/usr/bin/env bash
# Simulated: Livestock Barn Climate Control
set -euo pipefail
OUTFILE=""
VA=""
HP=""
MF=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --vent_ach) VA="$2"; shift 2 ;;
        --heater_pct) HP="$2"; shift 2 ;;
        --mist_freq) MF="$2"; shift 2 ;;
        --barn) shift 2 ;;
        --capacity) shift 2 ;;
        *) shift ;;
    esac
done
if [ -z "$VA" ] || [ -z "$HP" ] || [ -z "$MF" ]; then
    echo "Missing required factors" >&2; exit 1
fi
RESULT=$(awk -v VA="$VA" -v HP="$HP" -v MF="$MF" -v seed="$RANDOM" '
BEGIN {
    srand(seed); n1=(rand()-0.5)*2; n2=(rand()-0.5)*2;
    va=(VA-12)/8;hp=(HP-25)/25;mf=(MF-3)/3;
    ci=6+0.5*va+0.8*hp+0.5*mf-0.4*va*va-0.3*hp*hp-0.3*mf*mf+0.2*va*mf;
    eng=100+15*va+20*hp+5*mf+3*va*va+2*hp*hp+1*va*hp;
    if(ci<1)ci=1;if(ci>10)ci=10;if(eng<30)eng=30;
    printf "{\"comfort_index\": %.1f, \"energy_kwh_day\": %.0f}",ci+n1*0.3,eng+n2*5;
}')
mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

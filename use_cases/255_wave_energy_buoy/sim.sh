#!/usr/bin/env bash
# Simulated: Wave Energy Converter Tuning
set -euo pipefail
OUTFILE=""
BD=""
DR=""
PT=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --buoy_diam_m) BD="$2"; shift 2 ;;
        --draft_m) DR="$2"; shift 2 ;;
        --pto_damping) PT="$2"; shift 2 ;;
        --wave_height) shift 2 ;;
        --wave_period) shift 2 ;;
        *) shift ;;
    esac
done
if [ -z "$BD" ] || [ -z "$DR" ] || [ -z "$PT" ]; then
    echo "Missing required factors" >&2; exit 1
fi
RESULT=$(awk -v BD="$BD" -v DR="$DR" -v PT="$PT" -v seed="$RANDOM" '
BEGIN {
    srand(seed); n1=(rand()-0.5)*2; n2=(rand()-0.5)*2;
    bd=(BD-5.5)/2.5;dr=(DR-4)/2;pt=(PT-3000)/2000;
    pwr=30+12*bd+5*dr+8*pt-3*bd*bd-2*dr*dr-3*pt*pt+2*bd*pt;
    str_=15+4*bd+2*dr+3*pt+1*bd*bd+0.5*dr*dr+0.5*bd*dr;
    if(pwr<2)pwr=2;if(str_<5)str_=5;
    printf "{\"power_kw\": %.1f, \"stress_mpa\": %.0f}",pwr+n1*2,str_+n2*1;
}')
mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

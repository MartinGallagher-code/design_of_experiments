#!/usr/bin/env bash
# Simulated: Model Rocket Flight Optimization
set -euo pipefail
OUTFILE=""
IM=""
FA=""
NF=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --impulse_ns) IM="$2"; shift 2 ;;
        --fin_area_cm2) FA="$2"; shift 2 ;;
        --nose_fineness) NF="$2"; shift 2 ;;
        --body_diam) shift 2 ;;
        --recovery) shift 2 ;;
        *) shift ;;
    esac
done
if [ -z "$IM" ] || [ -z "$FA" ] || [ -z "$NF" ]; then
    echo "Missing required factors" >&2; exit 1
fi
RESULT=$(awk -v IM="$IM" -v FA="$FA" -v NF="$NF" -v seed="$RANDOM" '
BEGIN {
    srand(seed); n1=(rand()-0.5)*2; n2=(rand()-0.5)*2;
    im=(IM-22.5)/17.5;fa=(FA-50)/30;nf=(NF-5)/2;
    apo=150+80*im-15*fa+10*nf-10*im*im+5*fa*fa+3*nf*nf+5*im*nf;
    dft=50+20*im+10*fa-5*nf+5*im*im+3*im*fa;
    if(apo<20)apo=20;if(dft<5)dft=5;
    printf "{\"apogee_m\": %.0f, \"drift_m\": %.0f}",apo+n1*8,dft+n2*3;
}')
mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

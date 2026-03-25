#!/usr/bin/env bash
# Simulated: Tidal Turbine Placement
set -euo pipefail
OUTFILE=""
D=""
R=""
C=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --depth_m) D="$2"; shift 2 ;;
        --rotor_m) R="$2"; shift 2 ;;
        --cutin_ms) C="$2"; shift 2 ;;
        --site) shift 2 ;;
        --tidal_range) shift 2 ;;
        *) shift ;;
    esac
done
if [ -z "$D" ] || [ -z "$R" ] || [ -z "$C" ]; then
    echo "Missing required factors" >&2; exit 1
fi
RESULT=$(awk -v D="$D" -v R="$R" -v C="$C" -v seed="$RANDOM" '
BEGIN {
    srand(seed); n1=(rand()-0.5)*2; n2=(rand()-0.5)*2;
    d=(D-15)/10;r=(R-12.5)/7.5;c=(C-1.25)/0.75;
    mwh=500+100*d+200*r-50*c-30*d*d-40*r*r+20*d*r;
    imp=4+0.5*d+1.2*r-0.8*c+0.3*r*r+0.2*d*r;
    if(mwh<50)mwh=50;if(imp<1)imp=1;if(imp>10)imp=10;
    printf "{\"annual_mwh\": %.0f, \"impact_score\": %.1f}",mwh+n1*20,imp+n2*0.3;
}')
mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

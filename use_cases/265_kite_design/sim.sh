#!/usr/bin/env bash
# Simulated: Kite Aerodynamic Design
set -euo pipefail
OUTFILE=""
AR=""
BA=""
ST=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --aspect_ratio) AR="$2"; shift 2 ;;
        --bridle_angle_deg) BA="$2"; shift 2 ;;
        --sail_tension) ST="$2"; shift 2 ;;
        --material) shift 2 ;;
        --area) shift 2 ;;
        *) shift ;;
    esac
done
if [ -z "$AR" ] || [ -z "$BA" ] || [ -z "$ST" ]; then
    echo "Missing required factors" >&2; exit 1
fi
RESULT=$(awk -v AR="$AR" -v BA="$BA" -v ST="$ST" -v seed="$RANDOM" '
BEGIN {
    srand(seed); n1=(rand()-0.5)*2; n2=(rand()-0.5)*2;
    ar=(AR-2.75)/1.25;ba=(BA-32.5)/12.5;st=(ST-3)/2;
    lift=20+5*ar+3*ba+2*st-2*ar*ar-1.5*ba*ba-1*st*st+1*ar*ba;
    stab=6+0.3*ar-0.5*ba+1.0*st-0.3*ar*ar+0.2*ba*ba-0.3*st*st+0.2*ba*st;
    if(lift<5)lift=5;if(stab<1)stab=1;if(stab>10)stab=10;
    printf "{\"lift_n\": %.1f, \"stability_score\": %.1f}",lift+n1*1,stab+n2*0.3;
}')
mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

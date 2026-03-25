#!/usr/bin/env bash
# Simulated: RC Plane Trim Settings
set -euo pipefail
OUTFILE=""
EL=""
AD=""
TC=""
CG=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --elevator_pct) EL="$2"; shift 2 ;;
        --aileron_diff_pct) AD="$2"; shift 2 ;;
        --throttle_curve) TC="$2"; shift 2 ;;
        --cg_pct_mac) CG="$2"; shift 2 ;;
        --model) shift 2 ;;
        --wingspan) shift 2 ;;
        *) shift ;;
    esac
done
if [ -z "$EL" ] || [ -z "$AD" ] || [ -z "$TC" ] || [ -z "$CG" ]; then
    echo "Missing required factors" >&2; exit 1
fi
RESULT=$(awk -v EL="$EL" -v AD="$AD" -v TC="$TC" -v CG="$CG" -v seed="$RANDOM" '
BEGIN {
    srand(seed); n1=(rand()-0.5)*2; n2=(rand()-0.5)*2;
    el=(EL-0)/5;ad=(AD-20)/20;tc=(TC-75)/25;cg=(CG-30)/5;
    ft=12-0.5*el+0.2*ad-2*tc+0.3*cg-0.3*el*el+0.2*tc*tc;
    hs=6.5+0.3*el+0.5*ad+0.2*tc-0.8*cg-0.5*el*el-0.3*ad*ad-0.5*cg*cg+0.2*el*cg;
    if(ft<4)ft=4;if(hs<1)hs=1;if(hs>10)hs=10;
    printf "{\"flight_time_min\": %.1f, \"handling_score\": %.1f}",ft+n1*0.5,hs+n2*0.3;
}')
mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

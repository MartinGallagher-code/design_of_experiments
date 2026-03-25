#!/usr/bin/env bash
# Simulated: Solar Charge Controller Setup
set -euo pipefail
OUTFILE=""
AV=""
FV=""
MI=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --absorb_v) AV="$2"; shift 2 ;;
        --float_v) FV="$2"; shift 2 ;;
        --mppt_interval_sec) MI="$2"; shift 2 ;;
        --panel_wp) shift 2 ;;
        --battery) shift 2 ;;
        *) shift ;;
    esac
done
if [ -z "$AV" ] || [ -z "$FV" ] || [ -z "$MI" ]; then
    echo "Missing required factors" >&2; exit 1
fi
RESULT=$(awk -v AV="$AV" -v FV="$FV" -v MI="$MI" -v seed="$RANDOM" '
BEGIN {
    srand(seed); n1=(rand()-0.5)*2; n2=(rand()-0.5)*2;
    av=(AV-14.4)/0.4;fv=(FV-13.5)/0.3;mi=(MI-32.5)/27.5;
    eff=88+3*av+1*fv-2*mi-2*av*av-1*fv*fv-0.5*mi*mi+0.5*av*fv;
    ovr=3+2*av+0.5*fv+0.3*mi+1*av*av+0.3*fv*fv+0.2*av*fv;
    if(eff<70)eff=70;if(eff>98)eff=98;if(ovr<1)ovr=1;if(ovr>10)ovr=10;
    printf "{\"charge_efficiency_pct\": %.0f, \"overcharge_risk\": %.1f}",eff+n1*1,ovr+n2*0.3;
}')
mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

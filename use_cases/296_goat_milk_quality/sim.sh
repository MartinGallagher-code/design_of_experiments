#!/usr/bin/env bash
# Simulated: Goat Milk Quality Factors
set -euo pipefail
OUTFILE=""
CG=""
MF=""
PH=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --concentrate_g) CG="$2"; shift 2 ;;
        --milking_freq) MF="$2"; shift 2 ;;
        --pasture_hrs) PH="$2"; shift 2 ;;
        --breed) shift 2 ;;
        --lactation_week) shift 2 ;;
        *) shift ;;
    esac
done
if [ -z "$CG" ] || [ -z "$MF" ] || [ -z "$PH" ]; then
    echo "Missing required factors" >&2; exit 1
fi
RESULT=$(awk -v CG="$CG" -v MF="$MF" -v PH="$PH" -v seed="$RANDOM" '
BEGIN {
    srand(seed); n1=(rand()-0.5)*2; n2=(rand()-0.5)*2;
    cg=(CG-500)/300;mf=(MF-2)/1;ph=(PH-8)/4;
    bf=3.5+0.3*cg+0.2*mf+0.1*ph-0.2*cg*cg-0.1*mf*mf+0.1*cg*ph;
    scc=200-30*cg-50*mf+20*ph+10*cg*cg+15*mf*mf+5*cg*mf;
    if(bf<2)bf=2;if(bf>6)bf=6;if(scc<50)scc=50;
    printf "{\"butterfat_pct\": %.1f, \"scc_k_ml\": %.0f}",bf+n1*0.1,scc+n2*15;
}')
mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

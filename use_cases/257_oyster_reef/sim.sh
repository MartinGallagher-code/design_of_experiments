#!/usr/bin/env bash
# Simulated: Oyster Reef Substrate Design
set -euo pipefail
OUTFILE=""
RG=""
SD=""
EL=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --rugosity_cm) RG="$2"; shift 2 ;;
        --shell_depth_cm) SD="$2"; shift 2 ;;
        --elevation_m) EL="$2"; shift 2 ;;
        --species) shift 2 ;;
        --site) shift 2 ;;
        *) shift ;;
    esac
done
if [ -z "$RG" ] || [ -z "$SD" ] || [ -z "$EL" ]; then
    echo "Missing required factors" >&2; exit 1
fi
RESULT=$(awk -v RG="$RG" -v SD="$SD" -v EL="$EL" -v seed="$RANDOM" '
BEGIN {
    srand(seed); n1=(rand()-0.5)*2; n2=(rand()-0.5)*2;
    rg=(RG-6)/4;sd=(SD-25)/15;el=(EL-0)/1;
    set_=150+40*rg+30*sd-20*el-15*rg*rg-10*sd*sd-10*el*el+8*rg*sd;
    ht=5+1.5*rg+1*sd-0.8*el-0.5*rg*rg-0.3*sd*sd+0.3*rg*el;
    if(set_<20)set_=20;if(ht<0.5)ht=0.5;
    printf "{\"settlement_per_m2\": %.0f, \"reef_height_cm\": %.1f}",set_+n1*15,ht+n2*0.3;
}')
mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

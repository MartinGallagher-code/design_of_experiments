#!/usr/bin/env bash
# Simulated: Propeller Pitch Optimization
set -euo pipefail
OUTFILE=""
PT=""
DM=""
RP=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --pitch_deg) PT="$2"; shift 2 ;;
        --diameter_in) DM="$2"; shift 2 ;;
        --rpm) RP="$2"; shift 2 ;;
        --blades) shift 2 ;;
        --material) shift 2 ;;
        *) shift ;;
    esac
done
if [ -z "$PT" ] || [ -z "$DM" ] || [ -z "$RP" ]; then
    echo "Missing required factors" >&2; exit 1
fi
RESULT=$(awk -v PT="$PT" -v DM="$DM" -v RP="$RP" -v seed="$RANDOM" '
BEGIN {
    srand(seed); n1=(rand()-0.5)*2; n2=(rand()-0.5)*2;
    pt=(PT-13)/5;dm=(DM-11)/3;rp=(RP-6500)/2500;
    eff=75+3*pt+5*dm-2*rp-3*pt*pt-2*dm*dm-1*rp*rp+1.5*pt*dm;
    vib=4+0.5*pt+0.3*dm+1.2*rp+0.3*pt*pt+0.2*rp*rp+0.3*dm*rp;
    if(eff<40)eff=40;if(eff>95)eff=95;if(vib<1)vib=1;if(vib>10)vib=10;
    printf "{\"thrust_efficiency_pct\": %.0f, \"vibration_score\": %.1f}",eff+n1*2,vib+n2*0.3;
}')
mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

#!/usr/bin/env bash
# Simulated: Paper Airplane Distance
set -euo pipefail
OUTFILE=""
WS=""
NW=""
DH=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --wingspan_cm) WS="$2"; shift 2 ;;
        --nose_weight_g) NW="$2"; shift 2 ;;
        --dihedral_deg) DH="$2"; shift 2 ;;
        --paper) shift 2 ;;
        --fold) shift 2 ;;
        *) shift ;;
    esac
done
if [ -z "$WS" ] || [ -z "$NW" ] || [ -z "$DH" ]; then
    echo "Missing required factors" >&2; exit 1
fi
RESULT=$(awk -v WS="$WS" -v NW="$NW" -v DH="$DH" -v seed="$RANDOM" '
BEGIN {
    srand(seed); n1=(rand()-0.5)*2; n2=(rand()-0.5)*2;
    ws=(WS-22.5)/7.5;nw=(NW-1.5)/1.5;dh=(DH-7.5)/7.5;
    dist=8+2*ws+1.5*nw+0.5*dh-1*ws*ws-0.8*nw*nw-0.3*dh*dh+0.5*ws*nw;
    stab=6+0.3*ws+0.5*nw+1.0*dh-0.4*ws*ws-0.3*nw*nw-0.3*dh*dh+0.2*nw*dh;
    if(dist<1)dist=1;if(stab<1)stab=1;if(stab>10)stab=10;
    printf "{\"distance_m\": %.1f, \"stability_score\": %.1f}",dist+n1*0.5,stab+n2*0.3;
}')
mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

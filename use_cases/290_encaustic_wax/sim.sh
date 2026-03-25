#!/usr/bin/env bash
# Simulated: Encaustic Wax Painting
set -euo pipefail
OUTFILE=""
WT=""
DR=""
FD=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --wax_temp_c) WT="$2"; shift 2 ;;
        --damar_pct) DR="$2"; shift 2 ;;
        --fuse_dist_cm) FD="$2"; shift 2 ;;
        --wax) shift 2 ;;
        --support) shift 2 ;;
        *) shift ;;
    esac
done
if [ -z "$WT" ] || [ -z "$DR" ] || [ -z "$FD" ]; then
    echo "Missing required factors" >&2; exit 1
fi
RESULT=$(awk -v WT="$WT" -v DR="$DR" -v FD="$FD" -v seed="$RANDOM" '
BEGIN {
    srand(seed); n1=(rand()-0.5)*2; n2=(rand()-0.5)*2;
    wt=(WT-100)/20;dr=(DR-15)/10;fd=(FD-12.5)/7.5;
    adh=7+0.5*wt+0.8*dr-0.3*fd-0.5*wt*wt-0.3*dr*dr+0.2*wt*dr;
    crk=3+0.8*wt-0.5*dr+0.3*fd+0.4*wt*wt+0.2*dr*dr+0.2*wt*fd;
    if(adh<1)adh=1;if(adh>10)adh=10;if(crk<1)crk=1;if(crk>10)crk=10;
    printf "{\"adhesion_score\": %.1f, \"cracking_score\": %.1f}",adh+n1*0.3,crk+n2*0.3;
}')
mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

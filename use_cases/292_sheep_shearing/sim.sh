#!/usr/bin/env bash
# Simulated: Sheep Shearing Technique
set -euo pipefail
OUTFILE=""
CT=""
CR=""
BA=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --comb_teeth) CT="$2"; shift 2 ;;
        --cutter_rpm) CR="$2"; shift 2 ;;
        --blow_angle_deg) BA="$2"; shift 2 ;;
        --breed) shift 2 ;;
        --season) shift 2 ;;
        *) shift ;;
    esac
done
if [ -z "$CT" ] || [ -z "$CR" ] || [ -z "$BA" ]; then
    echo "Missing required factors" >&2; exit 1
fi
RESULT=$(awk -v CT="$CT" -v CR="$CR" -v BA="$BA" -v seed="$RANDOM" '
BEGIN {
    srand(seed); n1=(rand()-0.5)*2; n2=(rand()-0.5)*2;
    ct=(CT-13)/4;cr=(CR-2750)/750;ba=(BA-25)/15;
    sl=8+0.5*ct-0.3*cr+0.4*ba-0.3*ct*ct+0.2*cr*cr-0.2*ba*ba+0.15*ct*ba;
    nk=3-0.3*ct+0.5*cr+0.3*ba+0.2*ct*ct+0.3*cr*cr+0.2*cr*ba;
    if(sl<4)sl=4;if(nk<0)nk=0;
    printf "{\"staple_length_cm\": %.1f, \"nick_count\": %.1f}",sl+n1*0.3,nk+n2*0.3;
}')
mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

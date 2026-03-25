#!/usr/bin/env bash
# Simulated: Watercolor Wash Technique
set -euo pipefail
OUTFILE=""
WR=""
PW=""
BA=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --water_ratio) WR="$2"; shift 2 ;;
        --paper_wetness) PW="$2"; shift 2 ;;
        --brush_angle_deg) BA="$2"; shift 2 ;;
        --paper) shift 2 ;;
        --pigment) shift 2 ;;
        *) shift ;;
    esac
done
if [ -z "$WR" ] || [ -z "$PW" ] || [ -z "$BA" ]; then
    echo "Missing required factors" >&2; exit 1
fi
RESULT=$(awk -v WR="$WR" -v PW="$PW" -v BA="$BA" -v seed="$RANDOM" '
BEGIN {
    srand(seed); n1=(rand()-0.5)*2; n2=(rand()-0.5)*2;
    wr=(WR-5)/3;pw=(PW-3)/2;ba=(BA-37.5)/22.5;
    even=6+0.5*wr+1.0*pw+0.3*ba-0.4*wr*wr-0.5*pw*pw+0.2*wr*pw;
    bloom=4+0.5*wr+1.5*pw-0.3*ba+0.3*wr*wr+0.4*pw*pw+0.3*wr*pw;
    if(even<1)even=1;if(even>10)even=10;if(bloom<1)bloom=1;if(bloom>10)bloom=10;
    printf "{\"evenness\": %.1f, \"blooming\": %.1f}",even+n1*0.3,bloom+n2*0.3;
}')
mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

#!/usr/bin/env bash
# Simulated: Weather Balloon Launch Parameters
set -euo pipefail
OUTFILE=""
FV=""
BM=""
PW=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --fill_m3) FV="$2"; shift 2 ;;
        --balloon_g) BM="$2"; shift 2 ;;
        --payload_g) PW="$2"; shift 2 ;;
        --gas) shift 2 ;;
        --radiosonde) shift 2 ;;
        *) shift ;;
    esac
done
if [ -z "$FV" ] || [ -z "$BM" ] || [ -z "$PW" ]; then
    echo "Missing required factors" >&2; exit 1
fi
RESULT=$(awk -v FV="$FV" -v BM="$BM" -v PW="$PW" -v seed="$RANDOM" '
BEGIN {
    srand(seed); n1=(rand()-0.5)*2; n2=(rand()-0.5)*2;
    fv=(FV-1.4)/0.6;bm=(BM-750)/450;pw=(PW-300)/200;
    alt=28+3*fv+5*bm-2*pw-1*fv*fv-1.5*bm*bm+0.5*fv*bm;
    sw=15-3*fv+2*bm+4*pw+1*fv*fv+0.5*pw*pw+1*bm*pw;
    if(alt<15)alt=15;if(sw<3)sw=3;
    printf "{\"burst_alt_km\": %.1f, \"swing_deg\": %.0f}",alt+n1*1,sw+n2*1;
}')
mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

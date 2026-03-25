#!/usr/bin/env bash
# Simulated: Oscilloscope Measurement Setup
set -euo pipefail
OUTFILE=""
VD=""
BW=""
SR=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --v_div_mv) VD="$2"; shift 2 ;;
        --bw_mhz) BW="$2"; shift 2 ;;
        --sample_msa) SR="$2"; shift 2 ;;
        --probe) shift 2 ;;
        --coupling) shift 2 ;;
        *) shift ;;
    esac
done
if [ -z "$VD" ] || [ -z "$BW" ] || [ -z "$SR" ]; then
    echo "Missing required factors" >&2; exit 1
fi
RESULT=$(awk -v VD="$VD" -v BW="$BW" -v SR="$SR" -v seed="$RANDOM" '
BEGIN {
    srand(seed); n1=(rand()-0.5)*2; n2=(rand()-0.5)*2;
    vd=(VD-255)/245;bw=(BW-110)/90;sr=(SR-1050)/950;
    acc=95+1*vd+2*bw+1.5*sr-1*vd*vd-0.5*bw*bw-0.5*sr*sr+0.3*bw*sr;
    nf=5-1*vd+2*bw+0.5*sr+0.5*vd*vd+0.5*bw*bw+0.2*bw*sr;
    if(acc<80)acc=80;if(acc>100)acc=100;if(nf<0.5)nf=0.5;
    printf "{\"accuracy_pct\": %.1f, \"noise_floor_mv\": %.1f}",acc+n1*0.5,nf+n2*0.3;
}')
mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

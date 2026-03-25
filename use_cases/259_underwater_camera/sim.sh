#!/usr/bin/env bash
# Simulated: Underwater Camera Settings
set -euo pipefail
OUTFILE=""
WB=""
SP=""
PD=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --wb_shift_k) WB="$2"; shift 2 ;;
        --strobe_power_pct) SP="$2"; shift 2 ;;
        --port_dist_cm) PD="$2"; shift 2 ;;
        --depth) shift 2 ;;
        --housing) shift 2 ;;
        *) shift ;;
    esac
done
if [ -z "$WB" ] || [ -z "$SP" ] || [ -z "$PD" ]; then
    echo "Missing required factors" >&2; exit 1
fi
RESULT=$(awk -v WB="$WB" -v SP="$SP" -v PD="$PD" -v seed="$RANDOM" '
BEGIN {
    srand(seed); n1=(rand()-0.5)*2; n2=(rand()-0.5)*2;
    wb=(WB-7500)/2500;sp=(SP-62.5)/37.5;pd=(PD-17.5)/12.5;
    shrp=6.5+0.3*wb+0.8*sp-0.5*pd-0.2*wb*wb-0.3*sp*sp-0.3*pd*pd+0.2*sp*pd;
    col=6+1.0*wb+0.5*sp-0.3*pd-0.8*wb*wb-0.2*sp*sp+0.2*wb*sp;
    if(shrp<1)shrp=1;if(shrp>10)shrp=10;if(col<1)col=1;if(col>10)col=10;
    printf "{\"sharpness\": %.1f, \"color_accuracy\": %.1f}",shrp+n1*0.3,col+n2*0.3;
}')
mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

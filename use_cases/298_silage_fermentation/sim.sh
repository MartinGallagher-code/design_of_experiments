#!/usr/bin/env bash
# Simulated: Silage Fermentation Quality
set -euo pipefail
OUTFILE=""
CL=""
PD=""
IN=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --chop_mm) CL="$2"; shift 2 ;;
        --pack_kg_m3) PD="$2"; shift 2 ;;
        --inoculant_cfu_g) IN="$2"; shift 2 ;;
        --crop) shift 2 ;;
        --moisture) shift 2 ;;
        *) shift ;;
    esac
done
if [ -z "$CL" ] || [ -z "$PD" ] || [ -z "$IN" ]; then
    echo "Missing required factors" >&2; exit 1
fi
RESULT=$(awk -v CL="$CL" -v PD="$PD" -v IN="$IN" -v seed="$RANDOM" '
BEGIN {
    srand(seed); n1=(rand()-0.5)*2; n2=(rand()-0.5)*2;
    cl=(CL-15.5)/9.5;pd=(PD-225)/75;in_=(IN-500000)/500000;
    la=5+0.5*cl+1.0*pd+0.8*in_-0.3*cl*cl-0.3*pd*pd-0.2*in_*in_+0.2*pd*in_;
    dml=8-1*cl-2*pd-0.5*in_+0.5*cl*cl+0.5*pd*pd+0.3*cl*pd;
    if(la<2)la=2;if(la>8)la=8;if(dml<2)dml=2;if(dml>20)dml=20;
    printf "{\"lactic_acid_pct\": %.1f, \"dm_loss_pct\": %.1f}",la+n1*0.2,dml+n2*0.5;
}')
mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

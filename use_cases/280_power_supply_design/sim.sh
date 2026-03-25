#!/usr/bin/env bash
# Simulated: Linear Power Supply Regulation
set -euo pipefail
OUTFILE=""
TV=""
FC=""
DV=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --transformer_v) TV="$2"; shift 2 ;;
        --filter_uf) FC="$2"; shift 2 ;;
        --dropout_v) DV="$2"; shift 2 ;;
        --regulator) shift 2 ;;
        --output) shift 2 ;;
        *) shift ;;
    esac
done
if [ -z "$TV" ] || [ -z "$FC" ] || [ -z "$DV" ]; then
    echo "Missing required factors" >&2; exit 1
fi
RESULT=$(awk -v TV="$TV" -v FC="$FC" -v DV="$DV" -v seed="$RANDOM" '
BEGIN {
    srand(seed); n1=(rand()-0.5)*2; n2=(rand()-0.5)*2;
    tv=(TV-18)/6;fc=(FC-5500)/4500;dv=(DV-2.5)/1.5;
    lr=0.5-0.1*tv-0.05*fc+0.2*dv+0.05*tv*tv+0.02*fc*fc+0.05*dv*dv;
    rip=50-5*tv-15*fc+3*dv+2*tv*tv+3*fc*fc+1*dv*dv+1*tv*dv;
    if(lr<0.01)lr=0.01;if(rip<1)rip=1;
    printf "{\"load_reg_pct\": %.2f, \"ripple_mv\": %.0f}",lr+n1*0.02,rip+n2*2;
}')
mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

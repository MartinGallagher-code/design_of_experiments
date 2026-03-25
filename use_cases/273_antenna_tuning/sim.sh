#!/usr/bin/env bash
# Simulated: DIY Antenna Tuning
set -euo pipefail
OUTFILE=""
EL=""
HT=""
FP=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --element_pct) EL="$2"; shift 2 ;;
        --height_m) HT="$2"; shift 2 ;;
        --feedpoint_ohm) FP="$2"; shift 2 ;;
        --band) shift 2 ;;
        --type) shift 2 ;;
        *) shift ;;
    esac
done
if [ -z "$EL" ] || [ -z "$HT" ] || [ -z "$FP" ]; then
    echo "Missing required factors" >&2; exit 1
fi
RESULT=$(awk -v EL="$EL" -v HT="$HT" -v FP="$FP" -v seed="$RANDOM" '
BEGIN {
    srand(seed); n1=(rand()-0.5)*2; n2=(rand()-0.5)*2;
    el=(EL-100)/10;ht=(HT-6.5)/3.5;fp=(FP-50)/25;
    gain=5+0.3*el+0.8*ht-0.2*fp-1*el*el-0.3*ht*ht-0.2*fp*fp+0.2*el*ht;
    swr=1.5+0.8*el+0.2*ht+0.5*fp+0.5*el*el+0.2*fp*fp+0.2*el*fp;
    if(gain<0)gain=0;if(swr<1)swr=1;
    printf "{\"gain_dbi\": %.1f, \"swr\": %.2f}",gain+n1*0.2,swr+n2*0.1;
}')
mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

#!/usr/bin/env bash
# Simulated: Audio Amplifier Biasing
set -euo pipefail
OUTFILE=""
BI=""
SV=""
FB=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --bias_ma) BI="$2"; shift 2 ;;
        --supply_v) SV="$2"; shift 2 ;;
        --feedback_db) FB="$2"; shift 2 ;;
        --topology) shift 2 ;;
        --load) shift 2 ;;
        *) shift ;;
    esac
done
if [ -z "$BI" ] || [ -z "$SV" ] || [ -z "$FB" ]; then
    echo "Missing required factors" >&2; exit 1
fi
RESULT=$(awk -v BI="$BI" -v SV="$SV" -v FB="$FB" -v seed="$RANDOM" '
BEGIN {
    srand(seed); n1=(rand()-0.5)*2; n2=(rand()-0.5)*2;
    bi=(BI-55)/45;sv=(SV-25)/10;fb=(FB-20)/10;
    thd=0.1-0.03*bi+0.01*sv-0.05*fb+0.02*bi*bi+0.01*sv*sv+0.01*fb*fb-0.01*bi*fb;
    hr=6+1*bi+3*sv-0.5*fb-0.5*bi*bi-0.5*sv*sv+0.3*sv*fb;
    if(thd<0.001)thd=0.001;if(hr<1)hr=1;
    printf "{\"thd_pct\": %.3f, \"headroom_db\": %.1f}",thd+n1*0.005,hr+n2*0.3;
}')
mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

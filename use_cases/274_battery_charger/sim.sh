#!/usr/bin/env bash
# Simulated: Battery Charger Settings
set -euo pipefail
OUTFILE=""
CC=""
CV=""
TR=""
TL=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --charge_c) CC="$2"; shift 2 ;;
        --cutoff_v) CV="$2"; shift 2 ;;
        --trickle_pct) TR="$2"; shift 2 ;;
        --temp_limit_c) TL="$2"; shift 2 ;;
        --chemistry) shift 2 ;;
        --cells) shift 2 ;;
        *) shift ;;
    esac
done
if [ -z "$CC" ] || [ -z "$CV" ] || [ -z "$TR" ] || [ -z "$TL" ]; then
    echo "Missing required factors" >&2; exit 1
fi
RESULT=$(awk -v CC="$CC" -v CV="$CV" -v TR="$TR" -v TL="$TL" -v seed="$RANDOM" '
BEGIN {
    srand(seed); n1=(rand()-0.5)*2; n2=(rand()-0.5)*2;
    cc=(CC-1.25)/0.75;cv=(CV-4.2)/0.05;tr=(TR-6.5)/3.5;tl=(TL-42.5)/7.5;
    cap=92+3*cc+5*cv-0.5*tr-1*tl-1*cc*cc-2*cv*cv+0.5*cc*cv;
    cyc=500-80*cc-100*cv+10*tr+20*tl+20*cc*cc+30*cv*cv-10*cc*cv;
    if(cap<80)cap=80;if(cap>100)cap=100;if(cyc<100)cyc=100;
    printf "{\"capacity_pct\": %.0f, \"cycle_life\": %.0f}",cap+n1*1,cyc+n2*20;
}')
mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

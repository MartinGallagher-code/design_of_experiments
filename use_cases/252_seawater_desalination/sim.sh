#!/usr/bin/env bash
# Simulated: Seawater Desalination Efficiency
set -euo pipefail
OUTFILE=""
P=""
T=""
R=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --pressure_bar) P="$2"; shift 2 ;;
        --feed_temp_c) T="$2"; shift 2 ;;
        --recovery_pct) R="$2"; shift 2 ;;
        --membrane) shift 2 ;;
        --salinity) shift 2 ;;
        *) shift ;;
    esac
done
if [ -z "$P" ] || [ -z "$T" ] || [ -z "$R" ]; then
    echo "Missing required factors" >&2; exit 1
fi
RESULT=$(awk -v P="$P" -v T="$T" -v R="$R" -v seed="$RANDOM" '
BEGIN {
    srand(seed); n1=(rand()-0.5)*2; n2=(rand()-0.5)*2;
    p=(P-60)/10;t=(T-22.5)/7.5;r=(R-45)/10;
    flux=25+5*p+3*t-4*r-2*p*p-1*t*t-1.5*r*r+1*p*t;
    sec=3.5+0.5*p-0.3*t+0.8*r+0.2*p*p+0.3*r*r+0.2*p*r;
    if(flux<5)flux=5;if(sec<2)sec=2;
    printf "{\"permeate_lmh\": %.1f, \"sec_kwh_m3\": %.2f}",flux+n1*1,sec+n2*0.1;
}')
mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

#!/usr/bin/env bash
# Simulated: Glider Thermal Soaring Strategy
set -euo pipefail
OUTFILE=""
BK=""
EN=""
OF=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --bank_deg) BK="$2"; shift 2 ;;
        --entry_kts) EN="$2"; shift 2 ;;
        --offset_m) OF="$2"; shift 2 ;;
        --glider) shift 2 ;;
        --thermal_strength) shift 2 ;;
        *) shift ;;
    esac
done
if [ -z "$BK" ] || [ -z "$EN" ] || [ -z "$OF" ]; then
    echo "Missing required factors" >&2; exit 1
fi
RESULT=$(awk -v BK="$BK" -v EN="$EN" -v OF="$OF" -v seed="$RANDOM" '
BEGIN {
    srand(seed); n1=(rand()-0.5)*2; n2=(rand()-0.5)*2;
    bk=(BK-32.5)/12.5;en=(EN-55)/10;of=(OF-25)/25;
    clmb=2.5+0.3*bk-0.2*en-0.8*of-0.3*bk*bk+0.1*en*en-0.2*of*of+0.15*bk*en;
    circ=25-3*bk+1*en+0.5*of+1*bk*bk+0.5*en*en;
    if(clmb<0.2)clmb=0.2;if(circ<12)circ=12;
    printf "{\"climb_rate_ms\": %.2f, \"circle_time_sec\": %.0f}",clmb+n1*0.1,circ+n2*1;
}')
mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

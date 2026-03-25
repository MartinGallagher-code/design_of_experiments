#!/usr/bin/env bash
# Simulated: Printmaking Ink Viscosity
set -euo pipefail
OUTFILE=""
TK=""
OL=""
PG=""
MD=""
RP=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --tack_level) TK="$2"; shift 2 ;;
        --oil_pct) OL="$2"; shift 2 ;;
        --pigment_pct) PG="$2"; shift 2 ;;
        --modifier_pct) MD="$2"; shift 2 ;;
        --roller_pressure) RP="$2"; shift 2 ;;
        --method) shift 2 ;;
        --paper) shift 2 ;;
        *) shift ;;
    esac
done
if [ -z "$TK" ] || [ -z "$OL" ] || [ -z "$PG" ] || [ -z "$MD" ]; then
    echo "Missing required factors" >&2; exit 1
fi
RESULT=$(awk -v TK="$TK" -v OL="$OL" -v PG="$PG" -v MD="$MD" -v RP="$RP" -v seed="$RANDOM" '
BEGIN {
    srand(seed); n1=(rand()-0.5)*2; n2=(rand()-0.5)*2;
    tk=(TK-5)/3;ol=(OL-35)/15;pg=(PG-25)/10;md=(MD-5)/5;rp=(RP-3)/2;
    pq=6+0.5*tk-0.3*ol+0.8*pg-0.2*md+0.5*rp+0.2*tk*pg;
    tr=70+5*tk+3*ol+2*pg+1*md+5*rp+1*tk*rp;
    if(pq<1)pq=1;if(pq>10)pq=10;if(tr<40)tr=40;if(tr>100)tr=100;
    printf "{\"print_quality\": %.1f, \"transfer_pct\": %.0f}",pq+n1*0.3,tr+n2*2;
}')
mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

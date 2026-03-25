#!/usr/bin/env bash
# Simulated: Bronze Sculpture Patina
set -euo pipefail
OUTFILE=""
CH=""
TP=""
CT=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --chemical_pct) CH="$2"; shift 2 ;;
        --temp_c) TP="$2"; shift 2 ;;
        --coats) CT="$2"; shift 2 ;;
        --chemical) shift 2 ;;
        --metal) shift 2 ;;
        *) shift ;;
    esac
done
if [ -z "$CH" ] || [ -z "$TP" ] || [ -z "$CT" ]; then
    echo "Missing required factors" >&2; exit 1
fi
RESULT=$(awk -v CH="$CH" -v TP="$TP" -v CT="$CT" -v seed="$RANDOM" '
BEGIN {
    srand(seed); n1=(rand()-0.5)*2; n2=(rand()-0.5)*2;
    ch=(CH-17.5)/12.5;tp=(TP-50)/30;ct=(CT-3)/2;
    rich=6+1.0*ch+0.5*tp+0.8*ct-0.4*ch*ch-0.3*tp*tp-0.3*ct*ct+0.2*ch*tp;
    unif=6.5-0.3*ch+0.3*tp+0.5*ct-0.2*ch*ch-0.4*tp*tp-0.2*ct*ct+0.2*tp*ct;
    if(rich<1)rich=1;if(rich>10)rich=10;if(unif<1)unif=1;if(unif>10)unif=10;
    printf "{\"color_richness\": %.1f, \"uniformity\": %.1f}",rich+n1*0.3,unif+n2*0.3;
}')
mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

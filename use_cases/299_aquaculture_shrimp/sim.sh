#!/usr/bin/env bash
# Simulated: Shrimp Pond Management
set -euo pipefail
OUTFILE=""
SL=""
DN=""
CB=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --salinity_ppt) SL="$2"; shift 2 ;;
        --density_per_m2) DN="$2"; shift 2 ;;
        --carbon_g_m3) CB="$2"; shift 2 ;;
        --species) shift 2 ;;
        --pond) shift 2 ;;
        *) shift ;;
    esac
done
if [ -z "$SL" ] || [ -z "$DN" ] || [ -z "$CB" ]; then
    echo "Missing required factors" >&2; exit 1
fi
RESULT=$(awk -v SL="$SL" -v DN="$DN" -v CB="$CB" -v seed="$RANDOM" '
BEGIN {
    srand(seed); n1=(rand()-0.5)*2; n2=(rand()-0.5)*2;
    sl=(SL-20)/10;dn=(DN-75)/45;cb=(CB-12.5)/7.5;
    gr=2.0+0.3*sl-0.5*dn+0.3*cb-0.2*sl*sl-0.3*dn*dn-0.15*cb*cb+0.1*sl*cb;
    surv=80+3*sl-5*dn+2*cb-2*sl*sl-3*dn*dn-1*cb*cb+1*sl*dn;
    if(gr<0.5)gr=0.5;if(surv<40)surv=40;if(surv>98)surv=98;
    printf "{\"growth_g_wk\": %.2f, \"survival_pct\": %.0f}",gr+n1*0.1,surv+n2*2;
}')
mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

#!/usr/bin/env bash
# Simulated: Ceramic Glaze Firing
set -euo pipefail
OUTFILE=""
PT=""
HM=""
CR=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --peak_temp_c) PT="$2"; shift 2 ;;
        --hold_min) HM="$2"; shift 2 ;;
        --cool_rate_c_hr) CR="$2"; shift 2 ;;
        --kiln) shift 2 ;;
        --atmosphere) shift 2 ;;
        *) shift ;;
    esac
done
if [ -z "$PT" ] || [ -z "$HM" ] || [ -z "$CR" ]; then
    echo "Missing required factors" >&2; exit 1
fi
RESULT=$(awk -v PT="$PT" -v HM="$HM" -v CR="$CR" -v seed="$RANDOM" '
BEGIN {
    srand(seed); n1=(rand()-0.5)*2; n2=(rand()-0.5)*2;
    pt=(PT-1250)/50;hm=(HM-35)/25;cr=(CR-125)/75;
    surf=7+0.5*pt+0.8*hm-0.5*cr-0.5*pt*pt-0.3*hm*hm+0.2*pt*hm;
    col=6.5+0.3*pt+0.5*hm+0.4*cr-0.8*pt*pt-0.2*hm*hm-0.3*cr*cr+0.2*pt*cr;
    if(surf<1)surf=1;if(surf>10)surf=10;if(col<1)col=1;if(col>10)col=10;
    printf "{\"surface_quality\": %.1f, \"color_match\": %.1f}",surf+n1*0.3,col+n2*0.3;
}')
mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

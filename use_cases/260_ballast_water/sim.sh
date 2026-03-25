#!/usr/bin/env bash
# Simulated: Ballast Water Treatment
set -euo pipefail
OUTFILE=""
UV=""
FL=""
FR=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --uv_dose_mj_cm2) UV="$2"; shift 2 ;;
        --filter_um) FL="$2"; shift 2 ;;
        --flow_m3_hr) FR="$2"; shift 2 ;;
        --vessel) shift 2 ;;
        --regulation) shift 2 ;;
        *) shift ;;
    esac
done
if [ -z "$UV" ] || [ -z "$FL" ] || [ -z "$FR" ]; then
    echo "Missing required factors" >&2; exit 1
fi
RESULT=$(awk -v UV="$UV" -v FL="$FL" -v FR="$FR" -v seed="$RANDOM" '
BEGIN {
    srand(seed); n1=(rand()-0.5)*2; n2=(rand()-0.5)*2;
    uv=(UV-80)/40;fl=(FL-50)/25;fr=(FR-175)/125;
    rem=92+4*uv-3*fl-2*fr-1.5*uv*uv+1*fl*fl+0.5*fr*fr+1*uv*fl;
    tm=15-2*uv+1*fl-5*fr+0.5*uv*uv+0.3*fl*fl+1*fr*fr;
    if(rem<70)rem=70;if(rem>99.9)rem=99.9;if(tm<3)tm=3;
    printf "{\"removal_pct\": %.1f, \"treatment_min\": %.1f}",rem+n1*1,tm+n2*0.5;
}')
mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

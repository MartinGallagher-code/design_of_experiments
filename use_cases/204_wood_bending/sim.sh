#!/usr/bin/env bash
# Simulated: Steam Bending Parameters
set -euo pipefail

OUTFILE=""
SM=""
MC=""
BS=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --steam_min) SM="$2"; shift 2 ;;
        --moisture_pct) MC="$2"; shift 2 ;;
        --bend_speed) BS="$2"; shift 2 ;;
        --wood_species) shift 2 ;;
        --thickness_mm) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$SM" ] || [ -z "$MC" ] || [ -z "$BS" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v SM="$SM" -v MC="$MC" -v BS="$BS" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    sm = (SM - 75) / 45; mc = (MC - 22.5) / 7.5; bs = (BS - 3) / 2;
    rad = 15 - 3*sm - 2*mc + 2*bs + 1*sm*sm + 0.5*mc*mc + 0.3*bs*bs - 0.5*sm*mc;
    crack = 15 - 5*sm - 3*mc + 8*bs + 2*sm*sm + 1*bs*bs + 3*mc*bs;
    if (rad < 3) rad = 3; if (crack < 0) crack = 0; if (crack > 50) crack = 50;
    printf "{\"min_radius_cm\": %.1f, \"crack_rate_pct\": %.0f}", rad + n1*1, crack + n2*2;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

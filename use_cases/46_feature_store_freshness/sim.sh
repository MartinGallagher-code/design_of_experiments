#!/usr/bin/env bash
# Simulated: Feature Store Freshness
set -euo pipefail

OUTFILE=""
MI=""
CT=""
BS=""
OREP=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --materialization_interval_m) MI="$2"; shift 2 ;;
        --cache_ttl_s) CT="$2"; shift 2 ;;
        --batch_size) BS="$2"; shift 2 ;;
        --online_replicas) OREP="$2"; shift 2 ;;
        *) shift ;;
    esac
done

if [[ -z "$OUTFILE" ]] || [ -z "$MI" ] || [ -z "$CT" ] || [ -z "$BS" ] || [ -z "$OREP" ]; then
    echo "ERROR: missing required arguments" >&2
    exit 1
fi

RESULT=$(awk -v MI="$MI" -v CT="$CT" -v BS="$BS" -v OREP="$OREP" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    mi = (MI - 30.5) / 29.5;
    ct = (CT - 155) / 145;
    bs = (BS - 5050) / 4950;
    orep = (OREP - 3.5) / 2.5;
    slat = 5 + 2*mi + 3*ct - 4*orep + 0.5*bs + 1.5*ct*ct + 0.8*mi*ct - 1.2*orep*ct;
    fl = 3 + 8*mi - 2*ct + 1*bs - 0.5*orep + 2*mi*mi + 1.5*mi*bs;
    if (slat < 0.5) slat = 0.5; if (fl < 0.5) fl = 0.5;
    printf "{\"serving_latency_ms\": %.1f, \"freshness_lag_min\": %.1f}", slat + n1*0.8, fl + n2*1.0;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

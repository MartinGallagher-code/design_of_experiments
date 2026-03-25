#!/usr/bin/env bash
# Simulated: Feature Flag Evaluation
set -euo pipefail

OUTFILE=""
CT=""
RCS=""
SPI=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --cache_ttl_sec) CT="$2"; shift 2 ;;
        --rule_complexity_score) RCS="$2"; shift 2 ;;
        --sdk_polling_interval_sec) SPI="$2"; shift 2 ;;
        *) shift ;;
    esac
done

if [[ -z "$OUTFILE" ]] || [ -z "$CT" ] || [ -z "$RCS" ] || [ -z "$SPI" ]; then
    echo "ERROR: missing required arguments" >&2
    exit 1
fi

RESULT=$(awk -v CT="$CT" -v RCS="$RCS" -v SPI="$SPI" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    ct = (CT - 62.5) / 57.5;
    rcs = (RCS - 5.5) / 4.5;
    spi = (SPI - 155) / 145;
    lat = 150 - 40*ct + 50*rcs + 10*spi + 15*ct*ct + 20*rcs*rcs + 5*spi*spi - 8*ct*rcs;
    hit = 80 + 12*ct - 5*rcs - 3*spi - 4*ct*ct - 2*rcs*rcs + 2*ct*spi;
    if (lat < 10) lat = 10; if (hit > 99.5) hit = 99.5; if (hit < 40) hit = 40;
    printf "{\"evaluation_latency_us\": %.0f, \"cache_hit_rate_pct\": %.1f}", lat + n1*12, hit + n2*2;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

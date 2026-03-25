#!/usr/bin/env bash
# Simulated: Sourdough Starter Vitality
set -euo pipefail

OUTFILE=""
FR=""
AT=""
WG=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --feed_ratio) FR="$2"; shift 2 ;;
        --ambient_temp) AT="$2"; shift 2 ;;
        --whole_grain_pct) WG="$2"; shift 2 ;;
        --hydration) shift 2 ;;
        --feeding_schedule) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$FR" ] || [ -z "$AT" ] || [ -z "$WG" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v FR="$FR" -v AT="$AT" -v WG="$WG" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    fr = (FR - 3) / 2;
    at = (AT - 25) / 5;
    wg = (WG - 25) / 25;
    rise = 15 + 3*fr + 5*at + 2*wg - 1.5*fr*fr - 2*at*at + 1*fr*at + 0.5*at*wg;
    flav = 6.0 - 0.5*fr + 0.8*at + 1.2*wg + 0.3*fr*fr - 0.4*at*at + 0.3*fr*wg;
    if (rise < 1) rise = 1;
    if (flav < 1) flav = 1; if (flav > 10) flav = 10;
    printf "{\"rise_speed\": %.1f, \"flavor_complexity\": %.1f}", rise + n1*1.5, flav + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

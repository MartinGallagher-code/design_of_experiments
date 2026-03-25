#!/usr/bin/env bash
# Simulated: Candle Making Optimization
set -euo pipefail

OUTFILE=""
WS=""
FP=""
PT=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --wick_size) WS="$2"; shift 2 ;;
        --fragrance_pct) FP="$2"; shift 2 ;;
        --pour_temp_c) PT="$2"; shift 2 ;;
        --wax_type) shift 2 ;;
        --container) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$WS" ] || [ -z "$FP" ] || [ -z "$PT" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v WS="$WS" -v FP="$FP" -v PT="$PT" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    ws = (WS - 7) / 3;
    fp = (FP - 8) / 4;
    pt = (PT - 67.5) / 12.5;
    burn = 40 - 8*ws - 2*fp + 1*pt + 2*ws*ws - 0.5*fp*fp + 0.3*ws*fp;
    scent = 5.5 + 1.0*ws + 1.8*fp + 0.5*pt - 0.4*ws*ws - 0.3*fp*fp + 0.2*ws*fp;
    if (burn < 10) burn = 10;
    if (scent < 1) scent = 1; if (scent > 10) scent = 10;
    printf "{\"burn_hrs\": %.0f, \"scent_throw\": %.1f}", burn + n1*2, scent + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

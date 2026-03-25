#!/usr/bin/env bash
# Simulated: Party Planning Optimization
set -euo pipefail

OUTFILE=""
SG=""
FB=""
EH=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --sqft_per_guest) SG="$2"; shift 2 ;;
        --food_budget_pct) FB="$2"; shift 2 ;;
        --entertainment_hrs) EH="$2"; shift 2 ;;
        --guests) shift 2 ;;
        --event_type) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$SG" ] || [ -z "$FB" ] || [ -z "$EH" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v SG="$SG" -v FB="$FB" -v EH="$EH" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    sg = (SG - 27.5) / 12.5; fb = (FB - 45) / 15; eh = (EH - 2.5) / 1.5;
    sat = 6.5 + 0.5*sg + 1.0*fb + 0.8*eh - 0.3*sg*sg - 0.4*fb*fb - 0.3*eh*eh + 0.2*fb*eh;
    cost = 40 + 5*sg + 8*fb + 6*eh + 2*sg*sg + 1*fb*fb;
    if (sat < 1) sat = 1; if (sat > 10) sat = 10;
    if (cost < 15) cost = 15;
    printf "{\"satisfaction\": %.1f, \"cost_per_person\": %.0f}", sat + n1*0.3, cost + n2*3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

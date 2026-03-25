#!/usr/bin/env bash
# Simulated: Ginger Beer Fermentation
set -euo pipefail

OUTFILE=""
GG=""
SG=""
FD=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --ginger_g_L) GG="$2"; shift 2 ;;
        --sugar_g_L) SG="$2"; shift 2 ;;
        --ferm_days) FD="$2"; shift 2 ;;
        --starter) shift 2 ;;
        --lemon_juice) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$GG" ] || [ -z "$SG" ] || [ -z "$FD" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v GG="$GG" -v SG="$SG" -v FD="$FD" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    gg = (GG - 50) / 30; sg = (SG - 70) / 30; fd = (FD - 4.5) / 2.5;
    bite = 5.5 + 2.0*gg + 0.2*sg + 0.3*fd - 0.5*gg*gg + 0.1*sg*sg + 0.2*gg*fd;
    carb = 5.0 + 0.3*gg + 0.8*sg + 1.5*fd - 0.2*gg*gg - 0.3*sg*sg - 0.5*fd*fd + 0.2*sg*fd;
    if (bite < 1) bite = 1; if (bite > 10) bite = 10;
    if (carb < 1) carb = 1; if (carb > 10) carb = 10;
    printf "{\"ginger_bite\": %.1f, \"carbonation\": %.1f}", bite + n1*0.3, carb + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

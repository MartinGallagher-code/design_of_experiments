#!/usr/bin/env bash
# Simulated: Hard Cider Fermentation
set -euo pipefail

OUTFILE=""
PR=""
FT=""
SA=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --pitch_rate_g_L) PR="$2"; shift 2 ;;
        --ferm_temp_c) FT="$2"; shift 2 ;;
        --sugar_add_g_L) SA="$2"; shift 2 ;;
        --apple_variety) shift 2 ;;
        --yeast) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$PR" ] || [ -z "$FT" ] || [ -z "$SA" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v PR="$PR" -v FT="$FT" -v SA="$SA" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    pr = (PR - 1.25) / 0.75; ft = (FT - 17) / 5; sa = (SA - 25) / 25;
    flav = 7.0 + 0.3*pr - 0.5*ft + 0.2*sa - 0.4*pr*pr + 0.3*ft*ft - 0.3*sa*sa + 0.2*pr*ft;
    abv = 5.5 + 0.3*pr + 0.2*ft + 1.5*sa - 0.1*pr*pr + 0.2*sa*sa + 0.1*pr*sa;
    if (flav < 1) flav = 1; if (flav > 10) flav = 10;
    if (abv < 3) abv = 3; if (abv > 10) abv = 10;
    printf "{\"flavor_clarity\": %.1f, \"abv_pct\": %.1f}", flav + n1*0.3, abv + n2*0.2;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

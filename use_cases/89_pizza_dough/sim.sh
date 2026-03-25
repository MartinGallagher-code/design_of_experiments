#!/usr/bin/env bash
# Simulated: Pizza Dough Formulation
set -euo pipefail

OUTFILE=""
PP=""
YG=""
OM=""
FH=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --protein_pct) PP="$2"; shift 2 ;;
        --yeast_g) YG="$2"; shift 2 ;;
        --oil_ml) OM="$2"; shift 2 ;;
        --ferment_hrs) FH="$2"; shift 2 ;;
        --salt_pct) shift 2 ;;
        --water_temp) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$PP" ] || [ -z "$YG" ] || [ -z "$OM" ] || [ -z "$FH" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v PP="$PP" -v YG="$YG" -v OM="$OM" -v FH="$FH" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    pp = (PP - 12) / 2;
    yg = (YG - 4.5) / 2.5;
    om = (OM - 20) / 10;
    fh = (FH - 38) / 34;
    chew = 6.0 + 1.5*pp - 0.3*yg + 0.6*om + 0.8*fh + 0.4*pp*fh - 0.3*yg*om;
    bub = 5.5 + 0.5*pp + 1.2*yg - 0.4*om + 1.5*fh + 0.6*yg*fh + 0.3*pp*yg;
    if (chew < 1) chew = 1; if (chew > 10) chew = 10;
    if (bub < 1) bub = 1; if (bub > 10) bub = 10;
    printf "{\"chewiness\": %.1f, \"bubble_score\": %.1f}", chew + n1*0.5, bub + n2*0.4;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

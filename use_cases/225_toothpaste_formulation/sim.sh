#!/usr/bin/env bash
# Simulated: Toothpaste Cleaning Power
set -euo pipefail

OUTFILE=""
SI=""
FL=""
SL=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --silica_pct) SI="$2"; shift 2 ;;
        --fluoride_ppm) FL="$2"; shift 2 ;;
        --sls_pct) SL="$2"; shift 2 ;;
        --flavor) shift 2 ;;
        --ph) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$SI" ] || [ -z "$FL" ] || [ -z "$SL" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v SI="$SI" -v FL="$FL" -v SL="$SL" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    si = (SI - 17.5) / 7.5; fl = (FL - 1000) / 500; sl = (SL - 1.5) / 1;
    clean = 6.0 + 1.2*si + 0.5*fl + 0.8*sl - 0.3*si*si + 0.2*si*sl;
    rda = 80 + 30*si + 5*fl + 10*sl + 10*si*si + 3*si*sl;
    if (clean < 1) clean = 1; if (clean > 10) clean = 10;
    if (rda < 30) rda = 30; if (rda > 200) rda = 200;
    printf "{\"cleaning_score\": %.1f, \"rda_index\": %.0f}", clean + n1*0.3, rda + n2*5;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

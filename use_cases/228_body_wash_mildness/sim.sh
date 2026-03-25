#!/usr/bin/env bash
# Simulated: Body Wash Mildness Optimization
set -euo pipefail

OUTFILE=""
MS=""
MP=""
PH=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --mild_surfactant_pct) MS="$2"; shift 2 ;;
        --moisturizer_pct) MP="$2"; shift 2 ;;
        --product_ph) PH="$2"; shift 2 ;;
        --primary_surfactant) shift 2 ;;
        --fragrance) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$MS" ] || [ -z "$MP" ] || [ -z "$PH" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v MS="$MS" -v MP="$MP" -v PH="$PH" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    ms = (MS - 10) / 5; mp = (MP - 3) / 2; ph = (PH - 5.25) / 0.75;
    clean = 6.0 + 1.0*ms - 0.3*mp - 0.2*ph - 0.3*ms*ms + 0.2*ms*mp;
    barr = 4.0 + 0.8*ms - 0.5*mp - 0.6*ph + 0.2*ms*ms + 0.1*ph*ph + 0.2*ms*ph;
    if (clean < 1) clean = 1; if (clean > 10) clean = 10;
    if (barr < 1) barr = 1; if (barr > 10) barr = 10;
    printf "{\"cleansing_score\": %.1f, \"barrier_disruption\": %.1f}", clean + n1*0.3, barr + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

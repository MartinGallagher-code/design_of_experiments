#!/usr/bin/env bash
# Simulated: Hair Conditioner Formulation
set -euo pipefail

OUTFILE=""
CA=""
DM=""
PR=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --cetyl_pct) CA="$2"; shift 2 ;;
        --dimethicone_pct) DM="$2"; shift 2 ;;
        --protein_pct) PR="$2"; shift 2 ;;
        --base_ph) shift 2 ;;
        --preservative) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$CA" ] || [ -z "$DM" ] || [ -z "$PR" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v CA="$CA" -v DM="$DM" -v PR="$PR" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    ca = (CA - 4) / 2; dm = (DM - 1.75) / 1.25; pr = (PR - 1.25) / 0.75;
    detangle = 6.0 + 0.8*ca + 1.0*dm + 0.3*pr - 0.3*ca*ca - 0.4*dm*dm + 0.2*ca*dm;
    shine = 6.5 + 0.3*ca + 1.2*dm + 0.5*pr - 0.2*ca*ca - 0.5*dm*dm - 0.2*pr*pr + 0.2*dm*pr;
    if (detangle < 1) detangle = 1; if (detangle > 10) detangle = 10;
    if (shine < 1) shine = 1; if (shine > 10) shine = 10;
    printf "{\"detangle_score\": %.1f, \"shine_score\": %.1f}", detangle + n1*0.3, shine + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

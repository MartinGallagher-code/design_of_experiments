#!/usr/bin/env bash
# Simulated: Vinegar Mother Cultivation
set -euo pipefail

OUTFILE=""
AB=""
SA=""
TP=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --start_abv_pct) AB="$2"; shift 2 ;;
        --surface_area_cm2) SA="$2"; shift 2 ;;
        --temp_c) TP="$2"; shift 2 ;;
        --mother_source) shift 2 ;;
        --vessel) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$AB" ] || [ -z "$SA" ] || [ -z "$TP" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v AB="$AB" -v SA="$SA" -v TP="$TP" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    ab = (AB - 8.5) / 3.5; sa = (SA - 300) / 200; tp = (TP - 26) / 6;
    acid = 5.0 + 1.5*ab + 0.5*sa + 0.8*tp - 0.5*ab*ab - 0.2*sa*sa - 0.4*tp*tp + 0.2*ab*tp;
    off = 3.0 + 0.5*ab + 0.2*sa + 0.8*tp + 0.3*ab*ab + 0.2*tp*tp + 0.2*ab*tp;
    if (acid < 2) acid = 2; if (off < 1) off = 1; if (off > 10) off = 10;
    printf "{\"acidity_pct\": %.1f, \"off_flavor_score\": %.1f}", acid + n1*0.2, off + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

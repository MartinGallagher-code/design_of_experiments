#!/usr/bin/env bash
# Simulated: Kimchi Fermentation Timing
set -euo pipefail

OUTFILE=""
BP=""
FT=""
GP=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --brine_pct) BP="$2"; shift 2 ;;
        --ferm_temp_c) FT="$2"; shift 2 ;;
        --gochugaru_pct) GP="$2"; shift 2 ;;
        --cabbage_type) shift 2 ;;
        --garlic_pct) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$BP" ] || [ -z "$FT" ] || [ -z "$GP" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v BP="$BP" -v FT="$FT" -v GP="$GP" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    bp = (BP - 5.5) / 2.5; ft = (FT - 12) / 10; gp = (GP - 6.5) / 3.5;
    tang = 6.0 + 0.3*bp + 1.2*ft + 0.5*gp - 0.2*bp*bp - 0.5*ft*ft + 0.2*bp*ft;
    tex = 7.0 + 0.5*bp - 0.8*ft + 0.2*gp - 0.2*bp*bp + 0.3*ft*ft - 0.1*gp*gp + 0.2*bp*ft;
    if (tang < 1) tang = 1; if (tang > 10) tang = 10;
    if (tex < 1) tex = 1; if (tex > 10) tex = 10;
    printf "{\"tang_level\": %.1f, \"texture_score\": %.1f}", tang + n1*0.3, tex + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

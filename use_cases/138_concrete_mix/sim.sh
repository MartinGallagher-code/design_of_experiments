#!/usr/bin/env bash
# Simulated: DIY Concrete Mix Design
set -euo pipefail

OUTFILE=""
CP=""
WC=""
AG=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --cement_pct) CP="$2"; shift 2 ;;
        --water_cement_ratio) WC="$2"; shift 2 ;;
        --aggregate_mm) AG="$2"; shift 2 ;;
        --sand_type) shift 2 ;;
        --admixture) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$CP" ] || [ -z "$WC" ] || [ -z "$AG" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v CP="$CP" -v WC="$WC" -v AG="$AG" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    cp = (CP - 15) / 5;
    wc = (WC - 0.5) / 0.15;
    ag = (AG - 17.5) / 7.5;
    str_ = 25 + 8*cp - 10*wc + 2*ag - 2*cp*cp - 3*wc*wc + 1.5*cp*ag;
    cost = 90 + 20*cp - 5*wc - 3*ag + 5*cp*cp;
    if (str_ < 5) str_ = 5;
    if (cost < 50) cost = 50;
    printf "{\"strength_mpa\": %.1f, \"cost_per_m3\": %.0f}", str_ + n1*1.5, cost + n2*4;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

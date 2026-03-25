#!/usr/bin/env bash
# Simulated: Bread Baking Optimization
set -euo pipefail

OUTFILE=""
OT=""
HP=""
PT=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --oven_temp) OT="$2"; shift 2 ;;
        --hydration_pct) HP="$2"; shift 2 ;;
        --proof_time) PT="$2"; shift 2 ;;
        --flour_type) shift 2 ;;
        --salt_pct) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$OT" ] || [ -z "$HP" ] || [ -z "$PT" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v OT="$OT" -v HP="$HP" -v PT="$PT" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    ot = (OT - 230) / 30;
    hp = (HP - 70) / 10;
    pt = (PT - 75) / 45;
    crust = 6.5 + 1.2*ot - 0.4*hp + 0.8*pt - 0.6*ot*ot - 0.3*hp*hp + 0.5*ot*hp;
    crumb = 7.0 - 0.5*ot + 1.5*hp + 1.0*pt - 0.4*hp*hp - 0.7*pt*pt + 0.3*hp*pt;
    if (crust < 1) crust = 1; if (crust > 10) crust = 10;
    if (crumb < 1) crumb = 1; if (crumb > 10) crumb = 10;
    printf "{\"crust_score\": %.1f, \"crumb_score\": %.1f}", crust + n1*0.4, crumb + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

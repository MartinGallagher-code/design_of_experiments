#!/usr/bin/env bash
# Simulated: Tempeh Incubation Conditions
set -euo pipefail

OUTFILE=""
IT=""
HM=""
HP=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --incub_temp_c) IT="$2"; shift 2 ;;
        --humidity_pct) HM="$2"; shift 2 ;;
        --holes_per_cm2) HP="$2"; shift 2 ;;
        --bean) shift 2 ;;
        --starter) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$IT" ] || [ -z "$HM" ] || [ -z "$HP" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v IT="$IT" -v HM="$HM" -v HP="$HP" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    it = (IT - 31.5) / 3.5; hm = (HM - 75) / 15; hp = (HP - 1.75) / 1.25;
    cov = 80 + 5*it + 3*hm + 4*hp - 5*it*it - 2*hm*hm - 1*hp*hp + 1*it*hm;
    amm = 3.0 + 1.5*it + 0.3*hm - 0.5*hp + 1*it*it + 0.2*hm*hm + 0.3*it*hm;
    if (cov < 20) cov = 20; if (cov > 100) cov = 100;
    if (amm < 1) amm = 1; if (amm > 10) amm = 10;
    printf "{\"coverage_pct\": %.0f, \"ammonia_score\": %.1f}", cov + n1*3, amm + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

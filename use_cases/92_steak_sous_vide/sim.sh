#!/usr/bin/env bash
# Simulated: Steak Sous Vide Cooking
set -euo pipefail

OUTFILE=""
BT=""
CT=""
SE=""
RT=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --bath_temp) BT="$2"; shift 2 ;;
        --cook_time) CT="$2"; shift 2 ;;
        --sear_time) SE="$2"; shift 2 ;;
        --rest_time) RT="$2"; shift 2 ;;
        --cut) shift 2 ;;
        --thickness_mm) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$BT" ] || [ -z "$CT" ] || [ -z "$SE" ] || [ -z "$RT" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v BT="$BT" -v CT="$CT" -v SE="$SE" -v RT="$RT" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    bt = (BT - 57) / 5;
    ct = (CT - 150) / 90;
    se = (SE - 60) / 30;
    rt = (RT - 6) / 4;
    tend = 7.0 + 0.3*bt + 1.0*ct + 0.2*se + 0.3*rt - 0.5*bt*bt - 0.3*ct*ct + 0.2*bt*ct;
    juic = 7.5 - 0.8*bt - 0.3*ct - 0.5*se + 0.6*rt + 0.3*bt*bt + 0.2*se*rt;
    if (tend < 1) tend = 1; if (tend > 10) tend = 10;
    if (juic < 1) juic = 1; if (juic > 10) juic = 10;
    printf "{\"tenderness\": %.1f, \"juiciness\": %.1f}", tend + n1*0.4, juic + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

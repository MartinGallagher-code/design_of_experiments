#!/usr/bin/env bash
# Simulated: Vocal Mix Processing Chain
set -euo pipefail

OUTFILE=""
CR=""
EQ=""
RV=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --comp_ratio) CR="$2"; shift 2 ;;
        --eq_boost_khz) EQ="$2"; shift 2 ;;
        --reverb_send_db) RV="$2"; shift 2 ;;
        --mic) shift 2 ;;
        --genre) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$CR" ] || [ -z "$EQ" ] || [ -z "$RV" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v CR="$CR" -v EQ="$EQ" -v RV="$RV" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    cr = (CR - 5) / 3;
    eq = (EQ - 5) / 3;
    rv = (RV - -15) / 9;
    pres = 6.0 + 0.8*cr + 0.5*eq - 0.3*rv - 0.5*cr*cr - 0.3*eq*eq + 0.2*cr*eq;
    harsh = 3.5 + 0.5*cr + 1.2*eq + 0.2*rv + 0.3*cr*cr + 0.4*eq*eq + 0.2*cr*eq;
    if (pres < 1) pres = 1; if (pres > 10) pres = 10;
    if (harsh < 1) harsh = 1; if (harsh > 10) harsh = 10;
    printf "{\"presence_score\": %.1f, \"harshness\": %.1f}", pres + n1*0.3, harsh + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

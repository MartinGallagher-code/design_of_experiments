#!/usr/bin/env bash
# Simulated: PCR Amplification Efficiency
set -euo pipefail

OUTFILE=""
AT=""
PN=""
MG=""
CY=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --anneal_temp_c) AT="$2"; shift 2 ;;
        --primer_nm) PN="$2"; shift 2 ;;
        --mgcl2_mm) MG="$2"; shift 2 ;;
        --cycles) CY="$2"; shift 2 ;;
        --polymerase) shift 2 ;;
        --template_ng) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$AT" ] || [ -z "$PN" ] || [ -z "$MG" ] || [ -z "$CY" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v AT="$AT" -v PN="$PN" -v MG="$MG" -v CY="$CY" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    at = (AT - 58.5) / 6.5; pn = (PN - 400) / 200; mg = (MG - 2) / 1; cy = (CY - 32.5) / 7.5;
    yld = 6.0 + 0.3*at + 0.8*pn + 0.5*mg + 1.0*cy - 0.5*at*at - 0.3*pn*pn + 0.2*pn*cy;
    spec = 7.0 + 1.0*at - 0.5*pn - 0.8*mg - 0.5*cy - 0.3*at*at + 0.2*mg*mg + 0.2*at*mg;
    if (yld < 1) yld = 1; if (yld > 10) yld = 10;
    if (spec < 1) spec = 1; if (spec > 10) spec = 10;
    printf "{\"yield_score\": %.1f, \"specificity\": %.1f}", yld + n1*0.3, spec + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

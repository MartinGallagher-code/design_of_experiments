#!/usr/bin/env bash
# Simulated: Sunscreen SPF Formulation
set -euo pipefail

OUTFILE=""
ZO=""
MP=""
TH=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --zinc_oxide_pct) ZO="$2"; shift 2 ;;
        --moisturizer_pct) MP="$2"; shift 2 ;;
        --thickness_mg_cm2) TH="$2"; shift 2 ;;
        --base_type) shift 2 ;;
        --uva_filter) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$ZO" ] || [ -z "$MP" ] || [ -z "$TH" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v ZO="$ZO" -v MP="$MP" -v TH="$TH" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    zo = (ZO - 15) / 10;
    mp = (MP - 25) / 15;
    th = (TH - 1.75) / 0.75;
    spf = 30 + 12*zo + 2*mp + 8*th - 3*zo*zo - 1*mp*mp + 2*zo*th + 1*mp*th;
    grs = 4.5 + 1.5*zo + 1.8*mp + 0.5*th + 0.3*zo*zo + 0.2*mp*mp + 0.4*zo*mp;
    if (spf < 5) spf = 5;
    if (grs < 1) grs = 1; if (grs > 10) grs = 10;
    printf "{\"spf_value\": %.0f, \"greasiness\": %.1f}", spf + n1*2, grs + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

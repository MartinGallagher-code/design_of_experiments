#!/usr/bin/env bash
# Simulated: Raised Bed Soil Mix
set -euo pipefail

OUTFILE=""
PE=""
PL=""
CO=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --peat_pct) PE="$2"; shift 2 ;;
        --perlite_pct) PL="$2"; shift 2 ;;
        --compost_pct) CO="$2"; shift 2 ;;
        --bed_depth_cm) shift 2 ;;
        --remaining_topsoil) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$PE" ] || [ -z "$PL" ] || [ -z "$CO" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v PE="$PE" -v PL="$PL" -v CO="$CO" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    pe = (PE - 35) / 15;
    pl = (PL - 22.5) / 12.5;
    co = (CO - 30) / 15;
    drain = 50 + 8*pe + 15*pl - 5*co - 3*pe*pe - 4*pl*pl + 2*pe*pl;
    root = 3.5 + 0.4*pe + 0.3*pl + 0.8*co - 0.2*pe*pe - 0.15*pl*pl - 0.3*co*co + 0.15*pl*co;
    if (drain < 10) drain = 10;
    if (root < 0.5) root = 0.5;
    printf "{\"drainage_rate\": %.0f, \"root_growth\": %.2f}", drain + n1*5, root + n2*0.2;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

#!/usr/bin/env bash
# Simulated: Running Shoe Comfort Design
set -euo pipefail

OUTFILE=""
MS=""
FD=""
DR=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --midsole_mm) MS="$2"; shift 2 ;;
        --foam_density) FD="$2"; shift 2 ;;
        --drop_mm) DR="$2"; shift 2 ;;
        --upper) shift 2 ;;
        --outsole) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$MS" ] || [ -z "$FD" ] || [ -z "$DR" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v MS="$MS" -v FD="$FD" -v DR="$DR" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    ms = (MS - 30) / 10; fd = (FD - 225) / 75; dr = (DR - 6) / 6;
    cush = 6.5 + 1.2*ms - 0.8*fd + 0.3*dr - 0.4*ms*ms + 0.2*fd*fd + 0.2*ms*fd;
    ret = 60 + 3*ms - 5*fd + 1*dr + 2*fd*fd - 1*ms*ms + 1*ms*fd;
    if (cush < 1) cush = 1; if (cush > 10) cush = 10;
    if (ret < 30) ret = 30; if (ret > 85) ret = 85;
    printf "{\"cushion_score\": %.1f, \"energy_return_pct\": %.0f}", cush + n1*0.3, ret + n2*2;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

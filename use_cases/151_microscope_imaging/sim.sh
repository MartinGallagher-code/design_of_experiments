#!/usr/bin/env bash
# Simulated: Microscope Imaging Quality
set -euo pipefail

OUTFILE=""
MG=""
IL=""
CN=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --magnification) MG="$2"; shift 2 ;;
        --illumination_pct) IL="$2"; shift 2 ;;
        --condenser_na) CN="$2"; shift 2 ;;
        --specimen) shift 2 ;;
        --camera) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$MG" ] || [ -z "$IL" ] || [ -z "$CN" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v MG="$MG" -v IL="$IL" -v CN="$CN" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    mg = (MG - 55) / 45;
    il = (IL - 60) / 40;
    cn = (CN - 0.55) / 0.35;
    res = 2.0 - 0.8*mg - 0.2*il - 0.3*cn + 0.3*mg*mg + 0.1*il*il;
    aber = 4.0 + 1.5*mg + 0.5*il + 0.3*cn + 0.4*mg*mg - 0.2*cn*cn + 0.3*mg*il;
    if (res < 0.2) res = 0.2;
    if (aber < 1) aber = 1; if (aber > 10) aber = 10;
    printf "{\"resolution_um\": %.2f, \"aberration_score\": %.1f}", res + n1*0.1, aber + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

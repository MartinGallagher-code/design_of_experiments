#!/usr/bin/env bash
# Simulated essential oil blend — produces relaxation_score and antimicrobial_zone.
#
# Mixture design: lavender + eucalyptus + peppermint + tea_tree = 100%.
# Lavender dominates relaxation. Tea tree and eucalyptus dominate antimicrobial.
# Peppermint has moderate effects on both. Synergies between pairs.

set -euo pipefail

OUTFILE=""
LAV=""
EUC=""
PEP=""
TEA=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out)         OUTFILE="$2"; shift 2 ;;
        --lavender)    LAV="$2";     shift 2 ;;
        --eucalyptus)  EUC="$2";     shift 2 ;;
        --peppermint)  PEP="$2";     shift 2 ;;
        --tea_tree)    TEA="$2";     shift 2 ;;
        --carrier_oil) shift 2 ;;
        --dilution)    shift 2 ;;
        *)             shift ;;
    esac
done

if [[ -z "$OUTFILE" || -z "$LAV" || -z "$EUC" || -z "$PEP" || -z "$TEA" ]]; then
    echo "Usage: sim.sh --lavender L --eucalyptus E --peppermint P --tea_tree T --out FILE" >&2
    exit 1
fi

RESULT=$(awk -v lv="$LAV" -v eu="$EUC" -v pp="$PEP" -v tt="$TEA" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 4;
    n2 = (rand() - 0.5) * 2;

    # Normalize to fractions
    total = lv + eu + pp + tt;
    if (total < 1) total = 100;
    x1 = lv / total;
    x2 = eu / total;
    x3 = pp / total;
    x4 = tt / total;

    # Scheffe mixture model for relaxation score (pts, 0-100)
    rs = 85*x1 + 30*x2 + 55*x3 + 25*x4;
    rs = rs + 40*x1*x3 + 20*x1*x2 - 10*x2*x4 + 15*x3*x4;
    rs = rs + 30*x1*x2*x3 + 25*x1*x3*x4;
    rs = rs + n1;
    if (rs < 5) rs = 5;
    if (rs > 100) rs = 100;

    # Scheffe mixture model for antimicrobial zone (mm)
    az = 8*x1 + 22*x2 + 15*x3 + 28*x4;
    az = az + 12*x2*x4 + 8*x1*x4 + 6*x2*x3 + 4*x1*x3;
    az = az + 18*x2*x3*x4;
    az = az + n2;
    if (az < 2) az = 2;
    if (az > 40) az = 40;

    printf "{\"relaxation_score\": %.1f, \"antimicrobial_zone\": %.1f}", rs, az;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"

echo "  -> $(cat "$OUTFILE")"

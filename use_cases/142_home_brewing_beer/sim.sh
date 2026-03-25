#!/usr/bin/env bash
# Simulated: Home Brewing Beer
set -euo pipefail

OUTFILE=""
MT=""
BD=""
FT=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --mash_temp_c) MT="$2"; shift 2 ;;
        --boil_min) BD="$2"; shift 2 ;;
        --ferm_temp_c) FT="$2"; shift 2 ;;
        --yeast_strain) shift 2 ;;
        --og_target) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$MT" ] || [ -z "$BD" ] || [ -z "$FT" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v MT="$MT" -v BD="$BD" -v FT="$FT" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    mt = (MT - 66.5) / 3.5;
    bd = (BD - 67.5) / 22.5;
    ft = (FT - 19) / 3;
    flav = 7.0 + 0.5*mt + 0.8*bd - 0.3*ft - 1.0*mt*mt - 0.5*bd*bd - 0.8*ft*ft + 0.3*mt*bd;
    off = 3.0 + 0.5*mt - 0.3*bd + 1.2*ft + 0.3*mt*mt + 0.2*ft*ft + 0.4*mt*ft;
    if (flav < 1) flav = 1; if (flav > 10) flav = 10;
    if (off < 1) off = 1; if (off > 10) off = 10;
    printf "{\"flavor_balance\": %.1f, \"off_flavor_score\": %.1f}", flav + n1*0.3, off + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

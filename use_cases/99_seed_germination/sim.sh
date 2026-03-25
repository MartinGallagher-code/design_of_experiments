#!/usr/bin/env bash
# Simulated: Seed Germination Rate
set -euo pipefail

OUTFILE=""
ST=""
ML=""
SD=""
LH=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --soil_temp) ST="$2"; shift 2 ;;
        --moisture_level) ML="$2"; shift 2 ;;
        --seed_depth) SD="$2"; shift 2 ;;
        --light_hrs) LH="$2"; shift 2 ;;
        --seed_variety) shift 2 ;;
        --medium) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$ST" ] || [ -z "$ML" ] || [ -z "$SD" ] || [ -z "$LH" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v ST="$ST" -v ML="$ML" -v SD="$SD" -v LH="$LH" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    st = (ST - 21.5) / 6.5;
    ml = (ML - 50) / 20;
    sd = (SD - 15) / 10;
    lh = (LH - 12) / 4;
    germ = 75 + 8*st + 6*ml - 4*sd + 3*lh - 5*st*st - 3*ml*ml + 2*st*ml - 1.5*sd*lh;
    days = 7 - 1.5*st - 0.5*ml + 1.2*sd - 0.3*lh + 0.8*st*st + 0.3*sd*sd;
    if (germ < 0) germ = 0; if (germ > 100) germ = 100;
    if (days < 2) days = 2;
    printf "{\"germination_pct\": %.1f, \"days_to_emerge\": %.1f}", germ + n1*4, days + n2*0.5;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

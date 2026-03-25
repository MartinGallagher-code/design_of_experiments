#!/usr/bin/env bash
# Simulated: Beehive Honey Production
set -euo pipefail

OUTFILE=""
HS=""
SF=""
MT=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --hive_spacing_m) HS="$2"; shift 2 ;;
        --sugar_feed_kg) SF="$2"; shift 2 ;;
        --mite_treat_month) MT="$2"; shift 2 ;;
        --bee_species) shift 2 ;;
        --frames) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$HS" ] || [ -z "$SF" ] || [ -z "$MT" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v HS="$HS" -v SF="$SF" -v MT="$MT" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    hs = (HS - 5) / 3; sf = (SF - 5) / 5; mt = (MT - 6) / 3;
    honey = 25 + 3*hs + 5*sf - 2*mt - 1*hs*hs - 2*sf*sf + 0.5*hs*sf;
    health = 7.0 + 0.5*hs - 0.3*sf + 0.8*mt - 0.3*hs*hs + 0.2*sf*sf - 0.5*mt*mt + 0.2*sf*mt;
    if (honey < 5) honey = 5;
    if (health < 1) health = 1; if (health > 10) health = 10;
    printf "{\"honey_kg\": %.1f, \"colony_health\": %.1f}", honey + n1*2, health + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

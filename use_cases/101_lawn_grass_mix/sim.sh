#!/usr/bin/env bash
# Simulated: Lawn Grass Seed Mix
set -euo pipefail

OUTFILE=""
RG=""
FE=""
SR=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --ryegrass_pct) RG="$2"; shift 2 ;;
        --fescue_pct) FE="$2"; shift 2 ;;
        --seed_rate) SR="$2"; shift 2 ;;
        --remaining_bluegrass_pct) shift 2 ;;
        --mowing_height_mm) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$RG" ] || [ -z "$FE" ] || [ -z "$SR" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v RG="$RG" -v FE="$FE" -v SR="$SR" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    rg = (RG - 40) / 20;
    fe = (FE - 40) / 20;
    sr = (SR - 55) / 25;
    dens = 6.5 + 1.0*rg + 0.5*fe + 1.2*sr - 0.4*rg*rg - 0.3*fe*fe - 0.5*sr*sr + 0.3*rg*fe;
    drght = 5.5 - 0.8*rg + 1.5*fe + 0.3*sr + 0.2*rg*rg - 0.4*fe*fe + 0.2*fe*sr;
    if (dens < 1) dens = 1; if (dens > 10) dens = 10;
    if (drght < 1) drght = 1; if (drght > 10) drght = 10;
    printf "{\"density_score\": %.1f, \"drought_tolerance\": %.1f}", dens + n1*0.4, drght + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

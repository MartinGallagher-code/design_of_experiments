#!/usr/bin/env bash
# Simulated: Home Insulation Optimization
set -euo pipefail

OUTFILE=""
AR=""
WR=""
WU=""
AS=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --attic_r) AR="$2"; shift 2 ;;
        --wall_r) WR="$2"; shift 2 ;;
        --window_u) WU="$2"; shift 2 ;;
        --air_seal_ach) AS="$2"; shift 2 ;;
        --climate_zone) shift 2 ;;
        --house_sqft) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$AR" ] || [ -z "$WR" ] || [ -z "$WU" ] || [ -z "$AS" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v AR="$AR" -v WR="$WR" -v WU="$WU" -v AS="$AS" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    ar = (AR - 34) / 15;
    wr = (WR - 16) / 5;
    wu = (WU - 0.45) / 0.2;
    as_ = (AS - 5) / 3;
    cost = 1200 - 150*ar - 100*wr + 200*wu + 180*as_ + 30*ar*ar + 20*wr*wr + 40*wu*as_;
    comf = 6.5 + 0.8*ar + 0.6*wr - 1.0*wu - 0.8*as_ - 0.2*ar*ar + 0.3*wr*ar;
    if (cost < 300) cost = 300;
    if (comf < 1) comf = 1; if (comf > 10) comf = 10;
    printf "{\"annual_heat_cost\": %.0f, \"comfort_score\": %.1f}", cost + n1*30, comf + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

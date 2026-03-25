#!/usr/bin/env bash
# Simulated: Rabbit Hutch Enrichment
set -euo pipefail

OUTFILE=""
FA=""
PL=""
TR=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --floor_area_m2) FA="$2"; shift 2 ;;
        --platform_levels) PL="$2"; shift 2 ;;
        --toy_rotation_days) TR="$2"; shift 2 ;;
        --rabbits) shift 2 ;;
        --outdoor_access) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$FA" ] || [ -z "$PL" ] || [ -z "$TR" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v FA="$FA" -v PL="$PL" -v TR="$TR" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    fa = (FA - 4) / 2; pl = (PL - 2.5) / 1.5; tr = (TR - 4) / 3;
    act = 6.0 + 1.0*fa + 0.8*pl - 0.5*tr - 0.3*fa*fa - 0.2*pl*pl + 0.2*fa*pl;
    ster = 8 - 2*fa - 1.5*pl + 1*tr + 0.5*fa*fa + 0.3*tr*tr - 0.3*fa*tr;
    if (act < 1) act = 1; if (act > 10) act = 10;
    if (ster < 0) ster = 0; if (ster > 30) ster = 30;
    printf "{\"activity_index\": %.1f, \"stereotypy_pct\": %.1f}", act + n1*0.3, ster + n2*1;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

#!/usr/bin/env bash
# Simulated: pH Buffer Preparation
set -euo pipefail

OUTFILE=""
CN=""
AR=""
IS=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --concentration_mm) CN="$2"; shift 2 ;;
        --acid_base_ratio) AR="$2"; shift 2 ;;
        --ionic_strength_mm) IS="$2"; shift 2 ;;
        --buffer_system) shift 2 ;;
        --target_ph) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$CN" ] || [ -z "$AR" ] || [ -z "$IS" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v CN="$CN" -v AR="$AR" -v IS="$IS" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    cn = (CN - 55) / 45; ar = (AR - 1.25) / 0.75; is = (IS - 175) / 125;
    cap = 15 + 8*cn + 0.5*ar + 1*is - 2*cn*cn - 3*ar*ar + 0.5*cn*ar;
    temp = 0.005 + 0.001*cn + 0.002*ar + 0.001*is + 0.0005*ar*ar;
    if (cap < 1) cap = 1;
    if (temp < 0.001) temp = 0.001;
    printf "{\"buffer_capacity\": %.1f, \"temp_sensitivity\": %.4f}", cap + n1*0.5, temp + n2*0.0003;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

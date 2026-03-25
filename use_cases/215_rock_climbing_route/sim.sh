#!/usr/bin/env bash
# Simulated: Indoor Climbing Route Setting
set -euo pipefail

OUTFILE=""
HS=""
WA=""
RF=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --hold_spacing_cm) HS="$2"; shift 2 ;;
        --wall_angle_deg) WA="$2"; shift 2 ;;
        --rest_frequency) RF="$2"; shift 2 ;;
        --wall_height) shift 2 ;;
        --hold_set) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$HS" ] || [ -z "$WA" ] || [ -z "$RF" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v HS="$HS" -v WA="$WA" -v RF="$RF" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    hs = (HS - 35) / 15; wa = (WA - 15) / 15; rf = (RF - 3) / 2;
    qual = 6.5 + 0.3*hs + 0.8*wa + 0.5*rf - 0.4*hs*hs - 0.3*wa*wa - 0.3*rf*rf + 0.2*hs*wa;
    grade = 7.0 - 0.5*hs + 0.3*wa - 0.2*rf - 0.6*hs*hs - 0.4*wa*wa + 0.2*hs*rf;
    if (qual < 1) qual = 1; if (qual > 10) qual = 10;
    if (grade < 1) grade = 1; if (grade > 10) grade = 10;
    printf "{\"quality_rating\": %.1f, \"grade_accuracy\": %.1f}", qual + n1*0.3, grade + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

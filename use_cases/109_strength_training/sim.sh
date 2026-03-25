#!/usr/bin/env bash
# Simulated: Strength Training Program
set -euo pipefail

OUTFILE=""
ST=""
RP=""
RS=""
FQ=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --sets) ST="$2"; shift 2 ;;
        --reps) RP="$2"; shift 2 ;;
        --rest_sec) RS="$2"; shift 2 ;;
        --freq_per_week) FQ="$2"; shift 2 ;;
        --exercise) shift 2 ;;
        --trainee_level) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$ST" ] || [ -z "$RP" ] || [ -z "$RS" ] || [ -z "$FQ" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v ST="$ST" -v RP="$RP" -v RS="$RS" -v FQ="$FQ" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    st = (ST - 4.5) / 1.5;
    rp = (RP - 7.5) / 4.5;
    rs = (RS - 120) / 60;
    fq = (FQ - 3.5) / 1.5;
    str_ = 8 + 2*st - 1.5*rp + 1.2*rs + 1.5*fq - 0.5*st*st + 0.8*rp*rp - 0.3*rs*rs - 0.4*fq*fq + 0.5*st*fq;
    fat = 4.5 + 1.2*st + 0.8*rp - 0.6*rs + 1.5*fq + 0.3*st*st + 0.4*st*fq - 0.2*rs*fq;
    if (str_ < 1) str_ = 1;
    if (fat < 1) fat = 1; if (fat > 10) fat = 10;
    printf "{\"strength_gain\": %.1f, \"fatigue_score\": %.1f}", str_ + n1*1.0, fat + n2*0.4;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

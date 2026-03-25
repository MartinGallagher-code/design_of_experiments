#!/usr/bin/env bash
# Simulated: Koi Pond Water Management
set -euo pipefail

OUTFILE=""
TO=""
FD=""
FR=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --turnover_per_hr) TO="$2"; shift 2 ;;
        --fish_per_m3) FD="$2"; shift 2 ;;
        --feed_pct_bw) FR="$2"; shift 2 ;;
        --pond_volume) shift 2 ;;
        --filter_type) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$TO" ] || [ -z "$FD" ] || [ -z "$FR" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v TO="$TO" -v FD="$FD" -v FR="$FR" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    to = (TO - 1.75) / 1.25; fd = (FD - 3) / 2; fr = (FR - 2.5) / 1.5;
    color = 6.5 + 0.5*to - 0.3*fd + 0.4*fr - 0.3*to*to + 0.2*fd*fd - 0.3*fr*fr + 0.2*to*fd;
    growth = 1.5 + 0.3*to - 0.4*fd + 0.6*fr - 0.2*to*to - 0.2*fd*fd - 0.3*fr*fr + 0.15*fd*fr;
    if (color < 1) color = 1; if (color > 10) color = 10;
    if (growth < 0.2) growth = 0.2;
    printf "{\"color_vibrancy\": %.1f, \"growth_cm_mo\": %.2f}", color + n1*0.3, growth + n2*0.1;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

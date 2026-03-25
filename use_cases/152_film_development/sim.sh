#!/usr/bin/env bash
# Simulated: Film Development Process
set -euo pipefail

OUTFILE=""
DT=""
AG=""
DM=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --dev_temp_c) DT="$2"; shift 2 ;;
        --agitation_per_min) AG="$2"; shift 2 ;;
        --dev_time_min) DM="$2"; shift 2 ;;
        --film_type) shift 2 ;;
        --developer) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$DT" ] || [ -z "$AG" ] || [ -z "$DM" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v DT="$DT" -v AG="$AG" -v DM="$DM" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    dt = (DT - 21) / 3;
    ag = (AG - 3.5) / 2.5;
    dm = (DM - 10) / 4;
    tonal = 7.0 + 0.5*dt + 0.3*ag + 0.8*dm - 0.4*dt*dt - 0.3*ag*ag - 0.5*dm*dm + 0.2*dt*dm;
    grain = 4.0 + 0.8*dt + 0.6*ag + 0.4*dm + 0.3*dt*dt + 0.2*ag*ag + 0.2*dt*ag;
    if (tonal < 3) tonal = 3; if (tonal > 10) tonal = 10;
    if (grain < 1) grain = 1; if (grain > 10) grain = 10;
    printf "{\"tonal_range\": %.1f, \"grain_score\": %.1f}", tonal + n1*0.3, grain + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

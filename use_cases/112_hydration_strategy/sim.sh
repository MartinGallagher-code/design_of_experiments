#!/usr/bin/env bash
# Simulated: Athletic Hydration Strategy
set -euo pipefail

OUTFILE=""
FL=""
NA=""
CB=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --fluid_ml_hr) FL="$2"; shift 2 ;;
        --sodium_mg_L) NA="$2"; shift 2 ;;
        --carb_pct) CB="$2"; shift 2 ;;
        --exercise_type) shift 2 ;;
        --ambient_temp) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$FL" ] || [ -z "$NA" ] || [ -z "$CB" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v FL="$FL" -v NA="$NA" -v CB="$CB" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    fl = (FL - 500) / 300;
    na = (NA - 600) / 400;
    cb = (CB - 5) / 3;
    perf = 72 + 5*fl + 3*na + 4*cb - 3*fl*fl - 1.5*na*na - 2*cb*cb + 1.5*fl*cb + 1*na*cb;
    gi = 3 + 1.5*fl + 0.5*na + 1.2*cb + 0.8*fl*fl + 0.3*cb*cb + 0.5*fl*cb;
    if (perf < 40) perf = 40; if (perf > 100) perf = 100;
    if (gi < 1) gi = 1; if (gi > 10) gi = 10;
    printf "{\"performance_index\": %.0f, \"gi_distress\": %.1f}", perf + n1*3, gi + n2*0.4;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

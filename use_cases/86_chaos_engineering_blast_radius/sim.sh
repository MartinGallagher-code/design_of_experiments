#!/usr/bin/env bash
# Simulated: Chaos Engineering Blast Radius
set -euo pipefail

OUTFILE=""
FI=""
EDUR=""
SST=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --failure_injection_pct) FI="$2"; shift 2 ;;
        --experiment_duration_min) EDUR="$2"; shift 2 ;;
        --steady_state_threshold) SST="$2"; shift 2 ;;
        *) shift ;;
    esac
done

if [[ -z "$OUTFILE" ]] || [ -z "$FI" ] || [ -z "$EDUR" ] || [ -z "$SST" ]; then
    echo "ERROR: missing required arguments" >&2
    exit 1
fi

RESULT=$(awk -v FI="$FI" -v EDUR="$EDUR" -v SST="$SST" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    fi = (FI - 27.5) / 22.5;
    edur = (EDUR - 17.5) / 12.5;
    sst = (SST - 0.945) / 0.045;
    res = 70 + 8*fi + 5*edur + 10*sst - 3*fi*fi - 2*edur*edur - 4*sst*sst + 2*fi*edur + 3*fi*sst;
    blast = 3 + 4*fi + 2*edur - 1.5*sst + 1*fi*fi + 0.5*edur*edur + 0.8*fi*edur;
    if (res > 100) res = 100; if (res < 20) res = 20;
    if (blast < 1) blast = 1;
    printf "{\"resilience_score\": %.1f, \"blast_radius_services\": %.0f}", res + n1*3, blast + n2*1;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

#!/usr/bin/env bash
# Simulated: Deployment Canary Rollout
set -euo pipefail

OUTFILE=""
CP=""
EW=""
ET=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --canary_pct) CP="$2"; shift 2 ;;
        --evaluation_window_min) EW="$2"; shift 2 ;;
        --error_threshold_pct) ET="$2"; shift 2 ;;
        *) shift ;;
    esac
done

if [[ -z "$OUTFILE" ]] || [ -z "$CP" ] || [ -z "$EW" ] || [ -z "$ET" ]; then
    echo "ERROR: missing required arguments" >&2
    exit 1
fi

RESULT=$(awk -v CP="$CP" -v EW="$EW" -v ET="$ET" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    cp = (CP - 15) / 10;
    ew = (EW - 17.5) / 12.5;
    et = (ET - 2.75) / 2.25;
    safe = 75 + 5*cp + 10*ew - 8*et - 2*cp*cp - 3*ew*ew + 2*cp*ew - 4*et*et + 1.5*ew*et;
    dt = 10 + 3*cp + 8*ew + 2*et + 1*cp*ew + 0.5*ew*ew;
    if (safe > 100) safe = 100; if (safe < 30) safe = 30;
    if (dt < 3) dt = 3;
    printf "{\"rollout_safety_score\": %.1f, \"deployment_time_min\": %.1f}", safe + n1*3, dt + n2*1.5;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

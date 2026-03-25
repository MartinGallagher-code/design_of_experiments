#!/usr/bin/env bash
# Simulated: Water Well Drilling Parameters
set -euo pipefail

OUTFILE=""
DP=""
SS=""
GP=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --depth_m) DP="$2"; shift 2 ;;
        --screen_slot_mm) SS="$2"; shift 2 ;;
        --gravel_mm) GP="$2"; shift 2 ;;
        --aquifer) shift 2 ;;
        --casing_diam) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$DP" ] || [ -z "$SS" ] || [ -z "$GP" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v DP="$DP" -v SS="$SS" -v GP="$GP" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    dp = (DP - 37.5) / 22.5; ss = (SS - 1.25) / 0.75; gp = (GP - 5) / 3;
    flow = 40 + 15*dp + 10*ss + 5*gp - 3*dp*dp - 4*ss*ss + 2*dp*ss;
    turb = 5 - 1*dp + 3*ss + 2*gp + 1*ss*ss + 0.5*gp*gp + 1*ss*gp;
    if (flow < 5) flow = 5; if (turb < 0.5) turb = 0.5;
    printf "{\"flow_rate_lpm\": %.0f, \"turbidity_ntu\": %.1f}", flow + n1*3, turb + n2*0.5;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

#!/usr/bin/env bash
# Simulated: GitOps Sync Interval
set -euo pipefail

OUTFILE=""
SI=""
HCT=""
PE=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --sync_interval_sec) SI="$2"; shift 2 ;;
        --health_check_timeout) HCT="$2"; shift 2 ;;
        --prune_enabled) PE="$2"; shift 2 ;;
        *) shift ;;
    esac
done

if [[ -z "$OUTFILE" ]] || [ -z "$SI" ] || [ -z "$HCT" ] || [ -z "$PE" ]; then
    echo "ERROR: missing required arguments" >&2
    exit 1
fi

RESULT=$(awk -v SI="$SI" -v HCT="$HCT" -v PE="$PE" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    si = (SI - 165) / 135;
    hct = (HCT - 35) / 25;
    pe = (PE == "on") ? 1 : -1;
    ddd = 30 + 25*si + 5*hct - 3*pe + 4*si*si + 1.5*hct*hct + 2*si*hct;
    rec = 95 - 3*si - 2*hct + 2*pe - 1*si*si + 0.5*pe*hct;
    if (ddd < 5) ddd = 5; if (rec > 100) rec = 100; if (rec < 70) rec = 70;
    printf "{\"drift_detection_delay_sec\": %.0f, \"reconciliation_success_pct\": %.1f}", ddd + n1*4, rec + n2*1.5;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

#!/usr/bin/env bash
# Simulated: DDoS Mitigation Threshold
set -euo pipefail

OUTFILE=""
SR=""
CL=""
CM=""
GB=""
AW=""
WL=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --syn_rate_limit) SR="$2"; shift 2 ;;
        --connection_limit) CL="$2"; shift 2 ;;
        --challenge_mode) CM="$2"; shift 2 ;;
        --geo_blocking) GB="$2"; shift 2 ;;
        --anomaly_window_s) AW="$2"; shift 2 ;;
        --whitelist_size) WL="$2"; shift 2 ;;
        *) shift ;;
    esac
done

if [[ -z "$OUTFILE" ]] || [ -z "$SR" ] || [ -z "$CL" ] || [ -z "$CM" ] || [ -z "$GB" ]; then
    echo "ERROR: missing required arguments" >&2
    exit 1
fi

RESULT=$(awk -v SR="$SR" -v CL="$CL" -v CM="$CM" -v GB="$GB" -v AW="$AW" -v WL="$WL" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    sr = (SR - 25500) / 24500;
    cl = (CL - 5050) / 4950;
    cm = (CM == "javascript") ? 1 : -1;
    gb = (GB == "on") ? 1 : -1;
    aw = (AW - 155) / 145;
    wl = (WL - 5050) / 4950;
    det = 88 + 4*sr + 3*cl + 5*cm + 2*gb + 3*aw - 1*wl + 1.5*cm*aw;
    fp = 3 + 2*sr + 1.5*cl + 3*cm + 4*gb + 1*aw - 2*wl + 0.8*cm*gb;
    if (det > 100) det = 100; if (det < 50) det = 50;
    if (fp < 0.1) fp = 0.1;
    printf "{\"detection_rate\": %.1f, \"false_positive_pct\": %.2f}", det + n1*2, fp + n2*0.5;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

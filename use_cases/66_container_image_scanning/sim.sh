#!/usr/bin/env bash
# Simulated: Container Image Scanning
set -euo pipefail

OUTFILE=""
LP=""
VDC=""
MIS=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --layer_parallelism) LP="$2"; shift 2 ;;
        --vuln_db_cache_hours) VDC="$2"; shift 2 ;;
        --max_image_size_gb) MIS="$2"; shift 2 ;;
        *) shift ;;
    esac
done

if [[ -z "$OUTFILE" ]] || [ -z "$LP" ] || [ -z "$VDC" ] || [ -z "$MIS" ]; then
    echo "ERROR: missing required arguments" >&2
    exit 1
fi

RESULT=$(awk -v LP="$LP" -v VDC="$VDC" -v MIS="$MIS" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    lp = (LP - 4.5) / 3.5;
    vdc = (VDC - 12.5) / 11.5;
    mis = (MIS - 5.5) / 4.5;
    st = 45 - 15*lp + 5*vdc + 20*mis + 4*lp*lp + 2*vdc*vdc + 3*mis*mis - 3*lp*mis;
    det = 92 + 2*lp - 4*vdc + 1*mis - 1*lp*lp - 2*vdc*vdc + 0.5*lp*vdc;
    if (st < 3) st = 3; if (det > 100) det = 100; if (det < 60) det = 60;
    printf "{\"scan_time_sec\": %.1f, \"cve_detection_rate\": %.1f}", st + n1*3, det + n2*1.5;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

#!/usr/bin/env bash
# Simulated: Video Encoding Quality
set -euo pipefail

OUTFILE=""
BR=""
CF=""
GP=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --bitrate_mbps) BR="$2"; shift 2 ;;
        --crf) CF="$2"; shift 2 ;;
        --gop_frames) GP="$2"; shift 2 ;;
        --codec) shift 2 ;;
        --resolution) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$BR" ] || [ -z "$CF" ] || [ -z "$GP" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v BR="$BR" -v CF="$CF" -v GP="$GP" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    br = (BR - 27.5) / 22.5;
    cf = (CF - 23) / 5;
    gp = (GP - 67.5) / 52.5;
    vmaf = 85 + 5*br - 6*cf + 0.5*gp - 1.5*br*br - 2*cf*cf + 1*br*cf;
    fsize = 200 + 120*br - 40*cf - 10*gp + 20*br*br;
    if (vmaf < 50) vmaf = 50; if (vmaf > 100) vmaf = 100;
    if (fsize < 30) fsize = 30;
    printf "{\"vmaf_score\": %.0f, \"file_size_mb\": %.0f}", vmaf + n1*1.5, fsize + n2*10;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

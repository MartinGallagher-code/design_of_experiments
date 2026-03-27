#!/usr/bin/env bash
# Simulated ceramic glaze firing — produces surface_smoothness and color_accuracy responses.
#
# Model accounts for categorical factors (clay_type, cooling_rate) and ordinal (glaze_thickness).

set -euo pipefail

OUTFILE=""
CLAY=""
GLAZE=""
PEAK_TEMP=""
HOLD=""
COOLING=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out)              OUTFILE="$2";    shift 2 ;;
        --clay_type)        CLAY="$2";       shift 2 ;;
        --glaze_thickness)  GLAZE="$2";      shift 2 ;;
        --peak_temperature) PEAK_TEMP="$2";  shift 2 ;;
        --hold_time)        HOLD="$2";       shift 2 ;;
        --cooling_rate)     COOLING="$2";    shift 2 ;;
        --kiln_type)        shift 2 ;;
        *)                  shift ;;
    esac
done

if [[ -z "$OUTFILE" || -z "$CLAY" || -z "$GLAZE" || -z "$PEAK_TEMP" || -z "$HOLD" ]]; then
    echo "Usage: sim.sh --clay_type C --glaze_thickness G --peak_temperature T --hold_time H --cooling_rate CR --out FILE" >&2
    exit 1
fi

RESULT=$(awk -v clay="$CLAY" -v glaze="$GLAZE" -v temp="$PEAK_TEMP" -v hold="$HOLD" -v cool="$COOLING" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 5;
    n2 = (rand() - 0.5) * 2;

    # Encode clay_type: porcelain=2, stoneware=1, earthenware=0
    if (clay == "porcelain") clay_v = 2;
    else if (clay == "stoneware") clay_v = 1;
    else clay_v = 0;

    # Encode glaze_thickness: thin=0, medium=1, thick=2
    if (glaze == "thin") glaze_v = 0;
    else if (glaze == "medium") glaze_v = 1;
    else glaze_v = 2;

    # Encode cooling_rate: slow=0, fast=1
    cool_v = (cool == "fast") ? 1 : 0;

    # Coded continuous
    temp_c = (temp - 1175) / 75;
    hold_c = (hold - 60) / 30;

    # Surface smoothness: porcelain best, higher temp helps, medium glaze optimal
    ss = 65 + 8*clay_v + 6*temp_c + 3*hold_c;
    ss = ss - 4*(glaze_v - 1)*(glaze_v - 1) - 3*cool_v;
    ss = ss + 2*clay_v*temp_c - 2*temp_c*temp_c + n1;
    if (ss < 0) ss = 0;
    if (ss > 100) ss = 100;

    # Color accuracy (deltaE, lower=better): affected by hold time, cooling rate, clay
    ca = 8 - 1.5*hold_c + 3*cool_v - 0.8*clay_v;
    ca = ca + 2*temp_c*temp_c - 1.2*glaze_v + 0.5*temp_c*cool_v + n2;
    if (ca < 0.5) ca = 0.5;
    if (ca > 20) ca = 20;

    printf "{\"surface_smoothness\": %.2f, \"color_accuracy\": %.2f}", ss, ca;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"

echo "  -> $(cat "$OUTFILE")"

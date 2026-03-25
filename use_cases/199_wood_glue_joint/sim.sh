#!/usr/bin/env bash
# Simulated: Wood Glue Joint Strength
set -euo pipefail

OUTFILE=""
SR=""
CP=""
OT=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --spread_g_m2) SR="$2"; shift 2 ;;
        --clamp_psi) CP="$2"; shift 2 ;;
        --open_time_min) OT="$2"; shift 2 ;;
        --glue_type) shift 2 ;;
        --wood) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$SR" ] || [ -z "$CP" ] || [ -z "$OT" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v SR="$SR" -v CP="$CP" -v OT="$OT" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    sr = (SR - 175) / 75; cp = (CP - 150) / 100; ot = (OT - 5.5) / 4.5;
    str_ = 8.0 + 1.5*sr + 1.0*cp - 0.5*ot - 0.8*sr*sr - 0.5*cp*cp - 0.3*ot*ot + 0.3*sr*cp;
    cure = 4.0 - 0.3*sr + 0.2*cp + 0.5*ot + 0.2*sr*sr - 0.1*cp*cp + 0.15*sr*ot;
    if (str_ < 2) str_ = 2; if (cure < 1) cure = 1;
    printf "{\"shear_strength_mpa\": %.1f, \"cure_hrs\": %.1f}", str_ + n1*0.4, cure + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

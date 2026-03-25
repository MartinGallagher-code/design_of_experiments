#!/usr/bin/env bash
# Simulated: Lens Sharpness Testing
set -euo pipefail

OUTFILE=""
AF=""
FL=""
FD=""
ST=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --aperture_f) AF="$2"; shift 2 ;;
        --focal_length) FL="$2"; shift 2 ;;
        --focus_dist_m) FD="$2"; shift 2 ;;
        --stabilization) ST="$2"; shift 2 ;;
        --body) shift 2 ;;
        --iso) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$AF" ] || [ -z "$FL" ] || [ -z "$FD" ] || [ -z "$ST" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v AF="$AF" -v FL="$FL" -v FD="$FD" -v ST="$ST" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    af = (AF - 6.9) / 4.1;
    fl = (FL - 47) / 23;
    fd = (FD - 5.5) / 4.5;
    st = (ST == "on") ? 1 : -1;
    center = 80 + 5*af - 3*fl + 2*fd + 3*st - 8*af*af + 2*fl*fl + 1*af*fl;
    corner = 25 - 8*af + 5*fl - 2*fd + 1*st + 5*af*af + 2*fl*fl;
    if (center < 30) center = 30; if (center > 120) center = 120;
    if (corner < 5) corner = 5; if (corner > 60) corner = 60;
    printf "{\"center_lpmm\": %.0f, \"corner_falloff_pct\": %.0f}", center + n1*3, corner + n2*2;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

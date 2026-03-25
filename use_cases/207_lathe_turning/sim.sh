#!/usr/bin/env bash
# Simulated: Wood Lathe Turning Quality
set -euo pipefail

OUTFILE=""
SR=""
RD=""
GA=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --spindle_rpm) SR="$2"; shift 2 ;;
        --rest_mm) RD="$2"; shift 2 ;;
        --gouge_angle) GA="$2"; shift 2 ;;
        --wood) shift 2 ;;
        --blank_diam) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$SR" ] || [ -z "$RD" ] || [ -z "$GA" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v SR="$SR" -v RD="$RD" -v GA="$GA" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    sr = (SR - 1750) / 1250; rd = (RD - 9) / 6; ga = (GA - 45) / 15;
    surf = 6.5 + 0.8*sr - 0.5*rd + 0.4*ga - 0.5*sr*sr - 0.3*rd*rd - 0.3*ga*ga + 0.2*sr*ga;
    chat = 4.0 - 0.5*sr + 0.8*rd - 0.3*ga + 0.3*sr*sr + 0.2*rd*rd + 0.2*sr*rd;
    if (surf < 1) surf = 1; if (surf > 10) surf = 10;
    if (chat < 1) chat = 1; if (chat > 10) chat = 10;
    printf "{\"surface_quality\": %.1f, \"chatter_score\": %.1f}", surf + n1*0.3, chat + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

#!/usr/bin/env bash
# Simulated: Windshield Defog Strategy
set -euo pipefail

OUTFILE=""
FS=""
TS=""
AC=""
RC=""
RD=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --fan_speed) FS="$2"; shift 2 ;;
        --temp_setting) TS="$2"; shift 2 ;;
        --ac_on) AC="$2"; shift 2 ;;
        --recirc) RC="$2"; shift 2 ;;
        --rear_defrost) RD="$2"; shift 2 ;;
        --ambient_temp) shift 2 ;;
        --humidity) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$FS" ] || [ -z "$TS" ] || [ -z "$AC" ] || [ -z "$RC" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v FS="$FS" -v TS="$TS" -v AC="$AC" -v RC="$RC" -v RD="$RD" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    fs = (FS - 3) / 2;
    ts = (TS - 24) / 6;
    ac = (AC - 0.5) / 0.5;
    rc = (RC - 0.5) / 0.5;
    rd = (RD - 0.5) / 0.5;
    defog = 120 - 25*fs - 15*ts - 30*ac + 20*rc - 5*rd + 5*fs*ts + 10*ac*rc;
    energy = 300 + 80*fs + 40*ts + 120*ac + 10*rc + 60*rd + 15*fs*ac;
    if (defog < 15) defog = 15;
    if (energy < 100) energy = 100;
    printf "{\"defog_time_sec\": %.0f, \"energy_watts\": %.0f}", defog + n1*8, energy + n2*20;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

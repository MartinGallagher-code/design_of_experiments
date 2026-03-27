#!/usr/bin/env bash
# Simulated: Lithium-Ion Battery Cell Design (LHS with 25 samples, 6 factors, 3 responses)
set -euo pipefail

OUTFILE=""
CATH=""
ANOD=""
ELEC=""
SEP=""
CHRG=""
TAB=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --cathode_thickness) CATH="$2"; shift 2 ;;
        --anode_thickness) ANOD="$2"; shift 2 ;;
        --electrolyte_conc) ELEC="$2"; shift 2 ;;
        --separator_porosity) SEP="$2"; shift 2 ;;
        --charge_rate) CHRG="$2"; shift 2 ;;
        --tab_width) TAB="$2"; shift 2 ;;
        --cell_format) shift 2 ;;
        --temperature) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$CATH" ] || [ -z "$ANOD" ] || [ -z "$ELEC" ] || [ -z "$SEP" ] || [ -z "$CHRG" ] || [ -z "$TAB" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v CATH="$CATH" -v ANOD="$ANOD" -v ELEC="$ELEC" -v SEP="$SEP" -v CHRG="$CHRG" -v TAB="$TAB" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;
    n3 = (rand() - 0.5) * 2;

    # Normalize factors to [-1, 1]
    cath = (CATH - 100) / 50;
    anod = (ANOD - 90) / 30;
    elec = (ELEC - 1.1) / 0.3;
    sep = (SEP - 45) / 15;
    chrg = (CHRG - 1.75) / 1.25;
    tab = (TAB - 20) / 10;

    # Energy density (Wh/kg): thick electrodes help, high porosity hurts (more dead weight)
    ed = 220 + 25*cath + 15*anod + 8*elec - 10*sep - 5*chrg + 3*tab;
    ed = ed - 8*cath*cath - 5*anod*anod + 4*cath*anod;
    ed = ed + n1 * 5;
    if (ed < 100) ed = 100;
    if (ed > 350) ed = 350;

    # Power density (W/kg): thin electrodes, high porosity, wide tabs help
    pd = 800 - 80*cath - 40*anod + 30*elec + 60*sep + 50*chrg + 25*tab;
    pd = pd - 20*sep*sep + 15*elec*sep - 10*cath*chrg;
    pd = pd + n2 * 20;
    if (pd < 200) pd = 200;
    if (pd > 1500) pd = 1500;

    # Cycle life: moderate thickness, low charge rate, good electrolyte
    cl = 1200 - 150*chrg + 80*elec - 60*cath - 40*anod + 30*sep + 10*tab;
    cl = cl - 100*chrg*chrg - 50*elec*elec + 20*sep*elec;
    cl = cl + n3 * 40;
    if (cl < 200) cl = 200;
    if (cl > 3000) cl = 3000;

    printf "{\"energy_density\": %.1f, \"power_density\": %.0f, \"cycle_life\": %.0f}", ed, pd, cl;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

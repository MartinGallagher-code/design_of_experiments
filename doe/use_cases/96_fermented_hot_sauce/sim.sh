#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Fermented Hot Sauce Formulation
set -euo pipefail

OUTFILE=""
PS=""
SC=""
GP=""
FD=""
VP=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --pepper_shu) PS="$2"; shift 2 ;;
        --salt_pct) SC="$2"; shift 2 ;;
        --garlic_pct) GP="$2"; shift 2 ;;
        --ferm_days) FD="$2"; shift 2 ;;
        --vinegar_pct) VP="$2"; shift 2 ;;
        --ferm_temp) shift 2 ;;
        --jar_size) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$PS" ] || [ -z "$SC" ] || [ -z "$GP" ] || [ -z "$FD" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v PS="$PS" -v SC="$SC" -v GP="$GP" -v FD="$FD" -v VP="$VP" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    ps = (PS - 52500) / 47500;
    sc = (SC - 4) / 2;
    gp = (GP - 6) / 4;
    fd = (FD - 48.5) / 41.5;
    vp = (VP - 15) / 10;
    heat = 5.5 - 1.2*ps + 0.8*sc + 0.4*gp + 0.6*fd - 0.5*vp - 0.8*ps*ps + 0.3*sc*fd;
    umami = 5.0 + 0.3*ps + 0.5*sc + 1.0*gp + 1.5*fd - 0.3*vp + 0.4*gp*fd + 0.2*sc*gp;
    if (heat < 1) heat = 1; if (heat > 10) heat = 10;
    if (umami < 1) umami = 1; if (umami > 10) umami = 10;
    printf "{\"heat_balance\": %.1f, \"umami_depth\": %.1f}", heat + n1*0.4, umami + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

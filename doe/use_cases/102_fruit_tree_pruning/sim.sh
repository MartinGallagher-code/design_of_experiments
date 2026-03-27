#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Fruit Tree Pruning Strategy
set -euo pipefail

OUTFILE=""
PI=""
PM=""
BA=""
TR=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --prune_intensity) PI="$2"; shift 2 ;;
        --prune_month) PM="$2"; shift 2 ;;
        --branch_angle) BA="$2"; shift 2 ;;
        --thin_ratio) TR="$2"; shift 2 ;;
        --tree_age) shift 2 ;;
        --variety) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$PI" ] || [ -z "$PM" ] || [ -z "$BA" ] || [ -z "$TR" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v PI="$PI" -v PM="$PM" -v BA="$BA" -v TR="$TR" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    pi = (PI - 25) / 15;
    pm = (PM - 2) / 1;
    ba = (BA - 45) / 15;
    tr = (TR - 25) / 25;
    sz = 180 + 15*pi + 5*pm + 10*ba + 25*tr - 8*pi*pi + 5*pi*tr + 3*ba*tr;
    yl = 45 - 8*pi + 3*pm - 2*ba - 12*tr + 3*pi*pi + 2*pm*ba - 4*pi*tr;
    if (sz < 80) sz = 80;
    if (yl < 10) yl = 10;
    printf "{\"fruit_size_g\": %.0f, \"yield_kg\": %.1f}", sz + n1*10, yl + n2*3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

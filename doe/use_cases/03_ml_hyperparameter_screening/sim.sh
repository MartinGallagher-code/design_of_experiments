#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated ML training — accepts factors as positional arguments.
#
# Positional arg order matches factor order in config:
#   $1=learning_rate $2=batch_size $3=dropout $4=hidden_layers $5=optimizer
# Fixed factors follow, then --out <path>
#
# Model (hidden):
#   accuracy ~ 70 + 8*(lr_code) + 3*(bs_code) - 5*(dropout_code) + 4*(layers_code) + 6*(adam_bonus) + noise
#   training_time ~ 120 - 20*(lr_code) + 30*(bs_code_inv) + 15*(layers_code) + noise

set -euo pipefail

LR="${1:-0.001}";   shift || true
BS="${2:-32}";      shift || true
DO="${3:-0.1}";     shift || true
HL="${4:-2}";       shift || true
OPT="${5:-sgd}";    shift || true

OUTFILE=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        *)     shift ;;
    esac
done

if [[ -z "$OUTFILE" ]]; then
    echo "Error: --out <path> is required" >&2
    exit 1
fi

RESULT=$(awk -v lr="$LR" -v bs="$BS" -v do_val="$DO" -v hl="$HL" -v opt="$OPT" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 6;
    n2 = (rand() - 0.5) * 20;

    # Code to [-1, +1]
    lr_c = (lr == "0.1" || lr+0 >= 0.05) ? 1 : -1;
    bs_c = (bs == "256" || bs+0 >= 128) ? 1 : -1;
    do_c = (do_val == "0.5" || do_val+0 >= 0.3) ? 1 : -1;
    hl_c = (hl == "6" || hl+0 >= 4) ? 1 : -1;
    adam = (opt == "adam") ? 1 : 0;

    acc = 70 + 8*lr_c + 3*bs_c - 5*do_c + 4*hl_c + 6*adam + n1;
    if (acc > 99) acc = 99;
    if (acc < 30) acc = 30;

    tt = 120 - 20*lr_c - 10*bs_c + 15*hl_c + 8*do_c + n2;
    if (tt < 20) tt = 20;

    printf "{\"accuracy\": %.2f, \"training_time\": %.1f}", acc, tt;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

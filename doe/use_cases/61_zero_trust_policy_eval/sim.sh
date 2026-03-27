#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Zero Trust Policy Evaluation
set -euo pipefail

OUTFILE=""
PCT=""
CA=""
RSW=""
STO=""
MFA=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --policy_cache_ttl) PCT="$2"; shift 2 ;;
        --context_attributes) CA="$2"; shift 2 ;;
        --risk_score_weight) RSW="$2"; shift 2 ;;
        --session_timeout) STO="$2"; shift 2 ;;
        --mfa_frequency) MFA="$2"; shift 2 ;;
        *) shift ;;
    esac
done

if [[ -z "$OUTFILE" ]] || [ -z "$PCT" ] || [ -z "$CA" ] || [ -z "$RSW" ] || [ -z "$STO" ] || [ -z "$MFA" ]; then
    echo "ERROR: missing required arguments" >&2
    exit 1
fi

RESULT=$(awk -v PCT="$PCT" -v CA="$CA" -v RSW="$RSW" -v STO="$STO" -v MFA="$MFA" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    pct = (PCT - 155) / 145;
    ca = (CA - 7.5) / 4.5;
    rsw = (RSW - 0.5) / 0.4;
    sto = (STO - 1950) / 1650;
    mfa = (MFA - 12.5) / 11.5;
    lat = 25 - 12*pct + 8*ca + 3*rsw + 2*sto + 4*mfa + 2*pct*pct + 3*ca*ca - 2*pct*ca;
    sec = 72 - 5*pct + 8*ca + 10*rsw - 6*sto - 8*mfa + 3*rsw*ca - 2*sto*mfa;
    if (lat < 2) lat = 2; if (sec > 100) sec = 100; if (sec < 20) sec = 20;
    printf "{\"auth_latency_ms\": %.1f, \"security_score\": %.1f}", lat + n1*2, sec + n2*3;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

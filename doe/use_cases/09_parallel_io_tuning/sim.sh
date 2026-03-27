#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated parallel I/O benchmark — produces write_bw and read_bw.
#
# Hidden model:
#   write_bw ~ 5 GB/s base, boosted by more stripes, more aggregators,
#              collective_io=on, and larger stripe_size. Alignment helps slightly.
#   read_bw  ~ 8 GB/s base, similar pattern but higher baseline.

set -euo pipefail

OUTFILE=""
STRIPE_COUNT=""
STRIPE_SIZE=""
AGGREGATORS=""
COLLECTIVE_IO=""
ALIGNMENT=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out)            OUTFILE="$2";        shift 2 ;;
        --stripe_count)   STRIPE_COUNT="$2";   shift 2 ;;
        --stripe_size)    STRIPE_SIZE="$2";    shift 2 ;;
        --aggregators)    AGGREGATORS="$2";    shift 2 ;;
        --collective_io)  COLLECTIVE_IO="$2";  shift 2 ;;
        --alignment)      ALIGNMENT="$2";      shift 2 ;;
        --filesystem)     shift 2 ;;
        --file_size_gb)   shift 2 ;;
        *)                shift ;;
    esac
done

if [[ -z "$OUTFILE" || -z "$STRIPE_COUNT" || -z "$STRIPE_SIZE" || -z "$AGGREGATORS" || -z "$COLLECTIVE_IO" || -z "$ALIGNMENT" ]]; then
    echo "Usage: sim.sh --stripe_count V --stripe_size V --aggregators V --collective_io V --alignment V --out FILE" >&2
    exit 1
fi

RESULT=$(awk -v sc="$STRIPE_COUNT" -v ss="$STRIPE_SIZE" -v agg="$AGGREGATORS" \
             -v cio="$COLLECTIVE_IO" -v align="$ALIGNMENT" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    noise1 = (rand() - 0.5) * 0.8;
    noise2 = (rand() - 0.5) * 1.0;

    # Write bandwidth model (GB/s)
    wbw = 5.0;
    # More stripes spread I/O across OSTs
    wbw += (sc - 4) / 28.0 * 6.0;
    # Larger stripe size improves sequential throughput
    wbw += (ss - 1) / 15.0 * 3.5;
    # More aggregators improve collective performance
    wbw += (agg - 4) / 60.0 * 4.0;
    # Collective I/O reduces lock contention
    if (cio == "on") wbw += 3.2;
    # Alignment reduces partial-stripe writes
    wbw += (align - 1) / 3.0 * 1.5;
    # Interaction: collective_io + many aggregators is especially good
    if (cio == "on") wbw += (agg - 4) / 60.0 * 2.0;
    wbw += noise1;
    if (wbw < 0.5) wbw = 0.5;

    # Read bandwidth model (GB/s)
    rbw = 8.0;
    # More stripes help reads even more
    rbw += (sc - 4) / 28.0 * 8.0;
    # Larger stripe size
    rbw += (ss - 1) / 15.0 * 4.0;
    # Aggregators help reads
    rbw += (agg - 4) / 60.0 * 5.0;
    # Collective I/O helps reads
    if (cio == "on") rbw += 2.8;
    # Alignment
    rbw += (align - 1) / 3.0 * 1.2;
    rbw += noise2;
    if (rbw < 0.5) rbw = 0.5;

    printf "{\"write_bw\": %.2f, \"read_bw\": %.2f}", wbw, rbw;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"

echo "  -> $(cat "$OUTFILE")"

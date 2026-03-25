#!/usr/bin/env bash
# Simulated MPI collective benchmark — produces allreduce_latency and bandwidth.
#
# Hidden model:
#   latency ~ 50us base, reduced by ring algo (~-12us), increased by large msg_size,
#             affected by ppn, coll_tuning=on helps (~-8us), binding=core helps (~-5us)
#   bandwidth ~ 10 GB/s base, increased by large eager_limit and msg_size,
#               ring algo helps, more ppn slightly reduces per-process BW

set -euo pipefail

OUTFILE=""
MSG_SIZE=""
ALGORITHM=""
PPN=""
EAGER_LIMIT=""
BINDING=""
COLL_TUNING=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out)           OUTFILE="$2";      shift 2 ;;
        --msg_size)      MSG_SIZE="$2";     shift 2 ;;
        --algorithm)     ALGORITHM="$2";    shift 2 ;;
        --ppn)           PPN="$2";          shift 2 ;;
        --eager_limit)   EAGER_LIMIT="$2";  shift 2 ;;
        --binding)       BINDING="$2";      shift 2 ;;
        --coll_tuning)   COLL_TUNING="$2";  shift 2 ;;
        --nodes)         shift 2 ;;
        --mpi_impl)      shift 2 ;;
        *)               shift ;;
    esac
done

if [[ -z "$OUTFILE" || -z "$MSG_SIZE" || -z "$ALGORITHM" || -z "$PPN" || -z "$EAGER_LIMIT" || -z "$BINDING" || -z "$COLL_TUNING" ]]; then
    echo "Usage: sim.sh --msg_size V --algorithm V --ppn V --eager_limit V --binding V --coll_tuning V --out FILE" >&2
    exit 1
fi

RESULT=$(awk -v msg="$MSG_SIZE" -v algo="$ALGORITHM" -v ppn="$PPN" -v eager="$EAGER_LIMIT" \
             -v bind="$BINDING" -v coll="$COLL_TUNING" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    noise1 = (rand() - 0.5) * 6;
    noise2 = (rand() - 0.5) * 1.2;

    # Latency model (us)
    lat = 50.0;
    # Large messages increase latency significantly
    lat += (msg - 4096) / 1048576.0 * 35.0;
    # Ring algorithm is better for large messages
    if (algo == "ring") lat -= 12.0;
    # More processes per node increases contention
    lat += (ppn - 16) / 48.0 * 15.0;
    # Core binding reduces contention
    if (bind == "core") lat -= 5.0;
    # Collective tuning helps
    if (coll == "on") lat -= 8.0;
    # Larger eager limit helps small messages
    lat -= (eager - 4096) / 262144.0 * 6.0;
    lat += noise1;
    if (lat < 5) lat = 5;

    # Bandwidth model (GB/s)
    bw = 10.0;
    # Larger messages improve bandwidth utilization
    bw += (msg - 4096) / 1048576.0 * 12.0;
    # Larger eager limit helps
    bw += (eager - 4096) / 262144.0 * 4.0;
    # Ring algorithm slightly better for BW
    if (algo == "ring") bw += 2.5;
    # More ppn can saturate links
    bw -= (ppn - 16) / 48.0 * 3.0;
    # Coll tuning helps
    if (coll == "on") bw += 1.8;
    bw += noise2;
    if (bw < 0.5) bw = 0.5;

    printf "{\"allreduce_latency\": %.2f, \"bandwidth\": %.2f}", lat, bw;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"

echo "  -> $(cat "$OUTFILE")"

#!/usr/bin/env bash
# sim.sh -- Checkpoint/Restart I/O Optimization simulator
# Accepts double-dash arguments and writes a JSON results file.

set -euo pipefail

# ── Parse arguments ──────────────────────────────────────────────────────────
OUT=""
CHECKPOINT_INTERVAL=""
STRIPE_COUNT=""
BB_CAPACITY_PCT=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out)                  OUT="$2";                  shift 2 ;;
        --checkpoint_interval)  CHECKPOINT_INTERVAL="$2";  shift 2 ;;
        --stripe_count)         STRIPE_COUNT="$2";         shift 2 ;;
        --bb_capacity_pct)      BB_CAPACITY_PCT="$2";      shift 2 ;;
        # Ignore any fixed factors passed by the runner
        --*)                    shift 2 ;;
    esac
done

if [[ -z "$OUT" || -z "$CHECKPOINT_INTERVAL" || -z "$STRIPE_COUNT" || -z "$BB_CAPACITY_PCT" ]]; then
    echo "Usage: sim.sh --out FILE --checkpoint_interval MIN --stripe_count N --bb_capacity_pct PCT" >&2
    exit 1
fi

# ── Deterministic seed from the inputs (for reproducible noise) ───────────
SEED=$(echo "${CHECKPOINT_INTERVAL}_${STRIPE_COUNT}_${BB_CAPACITY_PCT}" | cksum | awk '{print $1}')

# ── Model ────────────────────────────────────────────────────────────────────
# Uses awk for floating-point arithmetic.
read -r THROUGHPUT DISRUPTION <<< "$(awk -v ci="$CHECKPOINT_INTERVAL" \
     -v sc="$STRIPE_COUNT" \
     -v bb="$BB_CAPACITY_PCT" \
     -v seed="$SEED" \
'BEGIN {
    srand(seed);

    # ── Normalize factors to [0, 1] ──
    ci_n = (ci - 5)  / (30 - 5);    # 0 = 5 min,  1 = 30 min
    sc_n = (sc - 4)  / (64 - 4);    # 0 = 4,      1 = 64
    bb_n = (bb - 25) / (100 - 25);  # 0 = 25%,    1 = 100%

    # ── write_throughput_GBs ──
    # base ~50 GB/s
    tp  = 50;
    # More stripes help logarithmically: up to +15 GB/s at 64 stripes
    tp += log(sc / 4 + 1) / log(64 / 4 + 1) * 15;
    # Higher burst-buffer allocation: up to +20 GB/s at 100%
    tp += bb_n * 20;
    # Longer intervals reduce contention: up to +5 GB/s at 30 min
    tp += ci_n * 5;
    # Interaction: high stripes + high bb = +10 GB/s
    tp += sc_n * bb_n * 10;
    # Noise +/- ~1.5 GB/s
    tp += (rand() - 0.5) * 3.0;

    # ── app_disruption_sec ──
    # base ~45 s
    dis  = 45;
    # More stripes reduce disruption by up to 15 s
    dis -= sc_n * 15;
    # Higher bb capacity reduces by up to 12 s
    dis -= bb_n * 12;
    # Shorter intervals mean more frequent (slightly longer) stalls
    dis -= ci_n * 4;
    # Interaction: high stripes + high bb = -8 s
    dis -= sc_n * bb_n * 8;
    # Noise +/- ~1 s
    dis += (rand() - 0.5) * 2.0;

    # Clamp to sensible ranges
    if (tp  < 10) tp  = 10;
    if (dis <  5) dis =  5;

    printf "%.2f %.2f\n", tp, dis;
}')"

# ── Write JSON output ────────────────────────────────────────────────────────
mkdir -p "$(dirname "$OUT")"
cat > "$OUT" <<EOF
{
    "write_throughput_GBs": ${THROUGHPUT},
    "app_disruption_sec": ${DISRUPTION}
}
EOF

echo "Checkpoint I/O simulation complete -> ${OUT}"

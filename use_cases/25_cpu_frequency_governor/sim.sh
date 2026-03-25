#!/usr/bin/env bash
# --------------------------------------------------------------------------
# sim.sh — Simulated CPU frequency governor tuning experiment
#
# Responses modelled:
#   throughput_normalized (%)  — application throughput vs max-frequency baseline
#   energy_delay_product (J*s) — energy * runtime (lower is better)
#
# Usage:
#   bash sim.sh --out <dir> --governor <gov> --min_freq_pct <pct> \
#               --energy_perf_bias <epb>
# --------------------------------------------------------------------------

set -euo pipefail

# ── Parse arguments ────────────────────────────────────────────────────────
OUT=""
GOVERNOR=""
MIN_FREQ_PCT=""
ENERGY_PERF_BIAS=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out)              OUT="$2";              shift 2 ;;
        --governor)         GOVERNOR="$2";         shift 2 ;;
        --min_freq_pct)     MIN_FREQ_PCT="$2";     shift 2 ;;
        --energy_perf_bias) ENERGY_PERF_BIAS="$2"; shift 2 ;;
        --*) shift 2 ;;  # ignore unknown fixed-factor flags
        *) shift ;;
    esac
done

if [[ -z "$OUT" || -z "$GOVERNOR" || -z "$MIN_FREQ_PCT" || -z "$ENERGY_PERF_BIAS" ]]; then
    echo "Usage: sim.sh --out <dir> --governor <gov> --min_freq_pct <pct> --energy_perf_bias <epb>" >&2
    exit 1
fi

mkdir -p "$(dirname "$OUT")"

# ── Seed a reproducible-ish PRNG from the inputs ──────────────────────────
hash_input="${GOVERNOR}_${MIN_FREQ_PCT}_${ENERGY_PERF_BIAS}"
SEED=$(echo -n "$hash_input" | cksum | awk '{print $1}')
RANDOM=$((SEED % 32768))

# Helper: pseudo-random float in [-1, 1]
rand_noise() {
    local r=$((RANDOM % 2000 - 1000))
    echo "scale=4; $r / 1000" | bc
}

# ── Normalise continuous factors to [0, 1] ─────────────────────────────────
# min_freq_pct:     40 → 0.0,  80 → 1.0
# energy_perf_bias:  0 → 0.0,  15 → 1.0
freq_norm=$(echo "scale=6; ($MIN_FREQ_PCT - 40) / 40" | bc)
epb_norm=$(echo "scale=6; $ENERGY_PERF_BIAS / 15" | bc)

# ── Governor indicator variables ────────────────────────────────────────────
gov_perf=0; gov_sched=0; gov_cons=0
case "$GOVERNOR" in
    performance)  gov_perf=1  ;;
    schedutil)    gov_sched=1 ;;
    conservative) gov_cons=1  ;;
esac

# ── Model: throughput_normalized (%) ────────────────────────────────────────
# Base                              ~85 %
# performance governor              +12 %
# schedutil governor                 +5 %
# Higher min_freq  (freq_norm=1)     +8 %
# Lower EPB        (epb_norm=0)      +6 %  (enters as -6*epb_norm)
# Interaction: performance + low EPB +3 %
# Quadratic penalty on extremes of continuous factors
noise1=$(rand_noise)
throughput=$(echo "scale=4; \
    85.0 \
    + 12.0 * $gov_perf \
    +  5.0 * $gov_sched \
    +  8.0 * $freq_norm \
    -  6.0 * $epb_norm \
    +  3.0 * $gov_perf * (1.0 - $epb_norm) \
    -  2.0 * ($freq_norm - 0.5) * ($freq_norm - 0.5) \
    -  1.5 * ($epb_norm  - 0.5) * ($epb_norm  - 0.5) \
    + $noise1 * 0.8 \
" | bc)

# ── Model: energy_delay_product (J*s) ──────────────────────────────────────
# Base                                 ~5000 J*s
# performance governor                 +800
# conservative governor                -600
# Higher min_freq  (freq_norm=1)       +400
# Higher EPB       (epb_norm=1)        -500 (saves energy but slower)
# Quadratic terms — sweet spot at moderate settings
# Interaction: schedutil + moderate freq → small bonus
noise2=$(rand_noise)
edp=$(echo "scale=4; \
    5000.0 \
    + 800.0  * $gov_perf \
    - 600.0  * $gov_cons \
    + 400.0  * $freq_norm \
    - 500.0  * $epb_norm \
    + 300.0  * ($freq_norm - 0.5) * ($freq_norm - 0.5) \
    + 250.0  * ($epb_norm  - 0.5) * ($epb_norm  - 0.5) \
    - 150.0  * $gov_sched * (1.0 - ($freq_norm - 0.5) * ($freq_norm - 0.5) * 4.0) \
    + $noise2 * 40.0 \
" | bc)

# ── Write JSON results ─────────────────────────────────────────────────────
cat > "$OUT" <<EOF
{
    "throughput_normalized": ${throughput},
    "energy_delay_product": ${edp}
}
EOF

echo "Results written to $OUT"
echo "  throughput_normalized = ${throughput} %"
echo "  energy_delay_product  = ${edp} J*s"

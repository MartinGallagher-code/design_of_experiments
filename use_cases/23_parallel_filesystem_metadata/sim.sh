#!/usr/bin/env bash
# sim.sh -- Simulator for parallel filesystem metadata operations
# Models Lustre MDS performance (file creates and stats) as a function
# of five tuning factors.  Outputs JSON with creates_per_sec and stat_per_sec.

set -euo pipefail

# ---------------------------------------------------------------------------
# Parse arguments
# ---------------------------------------------------------------------------
OUT=""
MDT_COUNT=""
DIR_STRIPE=""
CLIENT_CACHE=""
COMMIT_ON_SHARE=""
MDS_THREADS=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out)            OUT="$2";            shift 2 ;;
        --mdt_count)      MDT_COUNT="$2";      shift 2 ;;
        --dir_stripe)     DIR_STRIPE="$2";     shift 2 ;;
        --client_cache)   CLIENT_CACHE="$2";   shift 2 ;;
        --commit_on_share) COMMIT_ON_SHARE="$2"; shift 2 ;;
        --mds_threads)    MDS_THREADS="$2";    shift 2 ;;
        --*) shift 2 ;;  # ignore unknown fixed-factor flags
        *) shift ;;
    esac
done

if [[ -z "$OUT" ]]; then
    echo "Error: --out is required" >&2
    exit 1
fi

# ---------------------------------------------------------------------------
# Encode factor levels to numeric 0/1 scale
# ---------------------------------------------------------------------------
# mdt_count: 1 -> 0.0, 4 -> 1.0
mdt_norm=$(awk "BEGIN {printf \"%.6f\", ($MDT_COUNT - 1) / 3.0}")

# dir_stripe: off -> 0, on -> 1
dir_val=0; [[ "$DIR_STRIPE" == "on" ]] && dir_val=1

# client_cache: off -> 0, on -> 1
cache_val=0; [[ "$CLIENT_CACHE" == "on" ]] && cache_val=1

# commit_on_share: 0 -> 0, 1 -> 1
cos_val="$COMMIT_ON_SHARE"

# mds_threads: 64 -> 0.0, 512 -> 1.0
threads_norm=$(awk "BEGIN {printf \"%.6f\", ($MDS_THREADS - 64) / 448.0}")

# ---------------------------------------------------------------------------
# Model: creates_per_sec
#   base          ~50 000
#   mdt_count      +120 000  (linear with norm)
#   dir_stripe     +40 000
#   client_cache   +15 000
#   commit_on_share -25 000
#   mds_threads    +30 000
#   mdt*dir_stripe +20 000
# ---------------------------------------------------------------------------
creates=$(awk -v m="$mdt_norm" -v d="$dir_val" -v c="$cache_val" \
              -v cosh_val="$cos_val" -v t="$threads_norm" \
    "BEGIN {
        srand(systime() + PROCINFO[\"pid\"]);
        base   = 50000;
        effect = 120000*m + 40000*d + 15000*c - 25000*cosh_val + 30000*t;
        inter  = 20000 * m * d;
        noise  = (rand() - 0.5) * 4000;
        val    = base + effect + inter + noise;
        printf \"%.1f\", val;
    }")

# ---------------------------------------------------------------------------
# Model: stat_per_sec
#   base          ~200 000
#   mdt_count      +250 000
#   client_cache   +80 000
#   dir_stripe     +30 000
#   commit_on_share -40 000
#   mds_threads    +50 000
# ---------------------------------------------------------------------------
stats=$(awk -v m="$mdt_norm" -v d="$dir_val" -v c="$cache_val" \
            -v cosh_val="$cos_val" -v t="$threads_norm" \
    "BEGIN {
        srand(systime() + PROCINFO[\"pid\"] + 7);
        base   = 200000;
        effect = 250000*m + 30000*d + 80000*c - 40000*cosh_val + 50000*t;
        noise  = (rand() - 0.5) * 8000;
        val    = base + effect + noise;
        printf \"%.1f\", val;
    }")

# ---------------------------------------------------------------------------
# Write results
# ---------------------------------------------------------------------------
mkdir -p "$(dirname "$OUT")"
cat > "$OUT" <<EOF
{
    "creates_per_sec": $creates,
    "stat_per_sec": $stats
}
EOF

echo "Results written to $OUT"
echo "  creates_per_sec = $creates ops/s"
echo "  stat_per_sec    = $stats ops/s"

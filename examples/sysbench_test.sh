#!/usr/bin/env bash
# sysbench memory benchmark test script for DOE runner.
# Called by the generated runner with:
#   --threads <n> --memory_block_size <v> ... --time=<s> --out <path>

set -euo pipefail

# ── Parse arguments ──────────────────────────────────────────────────────────
THREADS=1
MEMORY_BLOCK_SIZE="1K"
MEMORY_TOTAL_SIZE="1G"
MEMORY_SCOPE_TYPE="global"
MEMORY_ACCESS_MODE="seq"
MEMORY_OPER="read"
RAND_TYPE="special"
TIME_SEC=10
OUTFILE=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --threads)            THREADS="$2";            shift 2 ;;
        --memory_block_size)  MEMORY_BLOCK_SIZE="$2";  shift 2 ;;
        --memory_total_size)  MEMORY_TOTAL_SIZE="$2";  shift 2 ;;
        --memory_scope_type)  MEMORY_SCOPE_TYPE="$2";  shift 2 ;;
        --memory_access_mode) MEMORY_ACCESS_MODE="$2"; shift 2 ;;
        --memory_oper)        MEMORY_OPER="$2";        shift 2 ;;
        --rand_type)          RAND_TYPE="$2";          shift 2 ;;
        --time=*)             TIME_SEC="${1#--time=}";  shift ;;
        --out)                OUTFILE="$2";             shift 2 ;;
        *) shift ;;
    esac
done

if [[ -z "$OUTFILE" ]]; then
    echo "Error: --out <path> is required" >&2
    exit 1
fi

# ── Run sysbench ─────────────────────────────────────────────────────────────
echo "  sysbench memory run --threads=$THREADS --memory-block-size=$MEMORY_BLOCK_SIZE \\"
echo "    --memory-total-size=$MEMORY_TOTAL_SIZE --memory-scope-type=$MEMORY_SCOPE_TYPE \\"
echo "    --memory-access-mode=$MEMORY_ACCESS_MODE --memory-oper=$MEMORY_OPER \\"
echo "    --rand-type=$RAND_TYPE --time=$TIME_SEC"

RAW_OUTPUT=$(sysbench memory run \
    --threads="$THREADS" \
    --memory-block-size="$MEMORY_BLOCK_SIZE" \
    --memory-total-size="$MEMORY_TOTAL_SIZE" \
    --memory-scope-type="$MEMORY_SCOPE_TYPE" \
    --memory-access-mode="$MEMORY_ACCESS_MODE" \
    --memory-oper="$MEMORY_OPER" \
    --rand-type="$RAND_TYPE" \
    --time="$TIME_SEC" 2>&1)

# ── Parse throughput (MiB/sec) ────────────────────────────────────────────────
# sysbench output contains a line like:
#   10240.00 MiB transferred (1234.57 MiB/sec)
THROUGHPUT=$(echo "$RAW_OUTPUT" | grep -oP '\(\K[0-9]+\.[0-9]+(?= MiB/sec\))' || true)

if [[ -z "$THROUGHPUT" ]]; then
    echo "Error: could not parse throughput from sysbench output:" >&2
    echo "$RAW_OUTPUT" >&2
    exit 1
fi

echo "  -> throughput=${THROUGHPUT} MiB/sec"

# ── Write result JSON ─────────────────────────────────────────────────────────
mkdir -p "$(dirname "$OUTFILE")"
cat > "$OUTFILE" <<EOF
{
    "response": $THROUGHPUT,
    "unit": "MiB/sec",
    "factors": {
        "threads": "$THREADS",
        "memory_block_size": "$MEMORY_BLOCK_SIZE",
        "memory_total_size": "$MEMORY_TOTAL_SIZE",
        "memory_scope_type": "$MEMORY_SCOPE_TYPE",
        "memory_access_mode": "$MEMORY_ACCESS_MODE",
        "memory_oper": "$MEMORY_OPER",
        "rand_type": "$RAND_TYPE"
    },
    "raw_output": $(echo "$RAW_OUTPUT" | python3 -c "import json,sys; print(json.dumps(sys.stdin.read()))")
}
EOF

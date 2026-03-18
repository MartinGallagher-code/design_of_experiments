#!/usr/bin/env bash
# Example test script stub.
# Accepts --<factor> <value> ... --out <path> arguments.
# In real use, replace this with your actual experiment runner.

set -euo pipefail

# Parse arguments
OUTFILE=""
declare -A FACTORS

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out)
            OUTFILE="$2"
            shift 2
            ;;
        --duration)
            DURATION="$2"
            shift 2
            ;;
        --*)
            KEY="${1#--}"
            FACTORS[$KEY]="$2"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

# Simulate an experiment response (random float in 0-100, seeded by factors)
SEED=0
for VAL in "${FACTORS[@]}"; do
    SEED=$(( (SEED * 31 + ${#VAL}) % 9973 ))
done
RESPONSE=$(awk "BEGIN { srand($SEED); printf \"%.4f\", rand() * 100 }")

# Write result JSON
mkdir -p "$(dirname "$OUTFILE")"
cat > "$OUTFILE" <<EOF
{
    "response": $RESPONSE,
    "factors": {$(for K in "${!FACTORS[@]}"; do echo "        \"$K\": \"${FACTORS[$K]}\","; done | sed '$ s/,$//')
    }
}
EOF

echo "  -> response=$RESPONSE written to $OUTFILE"

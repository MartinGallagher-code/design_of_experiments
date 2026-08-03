#!/usr/bin/env bash
# Merge all files in this directory (recursively) into one bundle.
# Text files are inlined verbatim; binary files are base64-encoded
# under a ===FILE-B64: marker.
#
# Usage: ./merge.sh [output_file] [--part-size SIZE]
#   output_file  bundle to write                  (default: bundle.txt)
#   --part-size  split into numbered parts of at
#                most SIZE each, e.g. 900k, 5M, 1048576
#
# With --part-size the bundle is written as bundle.part01.txt,
# bundle.part02.txt, ... instead of a single file. Parts are cut only on
# section boundaries, so no file's contents are ever straddled across two of
# them. Restore with either
#
#     ./split.sh                            # picks the parts up automatically
#     cat bundle.part*.txt > bundle.txt     # reassemble, then ./split.sh
#
# A single section larger than SIZE cannot be divided, so its part will
# exceed SIZE; merge.sh warns when that happens.

set -e
cd "$(dirname "$0")"

out="bundle.txt"
part_size=""
positional=0

while [ $# -gt 0 ]; do
    case "$1" in
        --part-size)
            [ $# -ge 2 ] || { echo "merge.sh: --part-size needs a value" >&2; exit 1; }
            part_size="$2"; shift 2 ;;
        --part-size=*)
            part_size="${1#--part-size=}"; shift ;;
        -h|--help)
            sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
        -*)
            echo "merge.sh: unknown option: $1" >&2; exit 1 ;;
        *)
            [ "$positional" -eq 0 ] || { echo "merge.sh: unexpected argument: $1" >&2; exit 1; }
            out="$1"; positional=1; shift ;;
    esac
done

# Accept 900k / 5M / raw byte counts.
to_bytes() {
    case "$1" in
        *[kK]) echo $(( ${1%[kK]} * 1024 )) ;;
        *[mM]) echo $(( ${1%[mM]} * 1024 * 1024 )) ;;
        *[!0-9]*) echo "merge.sh: bad size: $1" >&2; exit 1 ;;
        *) echo "$1" ;;
    esac
}

limit=0
if [ -n "$part_size" ]; then
    limit=$(to_bytes "$part_size")
    [ "$limit" -gt 0 ] || { echo "merge.sh: --part-size must be > 0" >&2; exit 1; }
fi

# Part names derive from the output name: bundle.txt -> bundle.partNN.txt
stem="${out%.*}"
ext="${out##*.}"
[ "$ext" = "$out" ] && ext="txt"

body=$(mktemp ./.merge.XXXXXX)
trap 'rm -f "$body" "$body".part* "$body".count ./.merge.*' EXIT

# Candidate files: everything but .git, the bundle, any parts from a previous
# run, and these two scripts.
candidates=$(mktemp ./.merge.XXXXXX)
find . -type d -name .git -prune -o -type f \
    ! -name "$(basename "$0")" ! -name "split.sh" ! -name "$out" \
    ! -name "$(basename "$stem").part*.$ext" ! -name '.merge.*' -print \
    | sort > "$candidates"

# Skip anything .gitignore covers, so caches and build artefacts never land in
# the bundle. merge.sh walks the filesystem rather than the index, so without
# this a stray __pycache__ or htmlcov/ silently triples the output. One git
# call for the whole list; check-ignore exits 1 when nothing matches.
keep="$candidates"
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    ignored=$(mktemp ./.merge.XXXXXX)
    keep=$(mktemp ./.merge.XXXXXX)
    git check-ignore --stdin < "$candidates" > "$ignored" 2>/dev/null || true
    grep -vxF -f "$ignored" "$candidates" > "$keep" || true
    rm -f "$ignored"
fi

while read -r f; do
    rel="${f#./}"
    if grep -Iq . "$f"; then
        printf '===FILE: %s===\n' "$rel"
        cat "$f"
    else
        printf '===FILE-B64: %s===\n' "$rel"
        base64 "$f"
    fi
    printf '===END===\n'
done < "$keep" > "$body"
rm -f "$candidates"
[ "$keep" = "$candidates" ] || rm -f "$keep"

if [ "$limit" -eq 0 ]; then
    mv "$body" "$out"
    trap - EXIT
    echo "Wrote $(wc -l < "$out") lines to $out"
    exit 0
fi

# Cut into parts on section boundaries. Each section is buffered whole, then
# placed in the current part if it still fits, otherwise in a fresh one.
awk -v limit="$limit" -v prefix="$body.part" '
  function flush_section(   i, f) {
    if (nsec == 0) return
    if (partbytes > 0 && partbytes + secbytes > limit) { part++; partbytes = 0 }
    if (secbytes > limit && partbytes == 0)
      printf "merge.sh: section larger than part size, part %02d will exceed it: %s\n", \
        part, secname > "/dev/stderr"
    f = sprintf("%s%02d", prefix, part)
    for (i = 1; i <= nsec; i++) print sec[i] >> f
    close(f)
    partbytes += secbytes
    nsec = 0; secbytes = 0
  }
  BEGIN { part = 1 }
  /^===(FILE|FILE-B64): .*===$/ { flush_section(); secname = $0 }
  { sec[++nsec] = $0; secbytes += length($0) + 1 }
  END { flush_section(); print part }
' "$body" > "$body.count"

total=$(tail -1 "$body.count")

n=0
for p in "$body".part*; do
    n=$((n + 1))
    target=$(printf '%s.part%02d.%s' "$stem" "$n" "$ext")
    {
        printf '# %s -- part %d of %d\n' "$(basename "$out")" "$n" "$total"
        printf '# Concatenate every part in order and expand with split.sh.\n'
        cat "$p"
    } > "$target"
    echo "Wrote $target ($(wc -c < "$target") bytes, $(wc -l < "$target") lines)"
done

rm -f "$body" "$body".part* "$body".count
trap - EXIT
echo "Wrote $total part(s) of at most $part_size each"

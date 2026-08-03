#!/usr/bin/env bash
# Expand a bundle produced by merge.sh back into individual files.
# Handles both text (===FILE:) and base64 (===FILE-B64:) sections.
#
# Usage: ./split.sh [bundle_file ...]   (default: bundle.txt, or its parts)
#
# With no argument, bundle.txt is used if it exists; otherwise the numbered
# parts written by "merge.sh --part-size" (bundle.part01.txt, ...) are
# expanded together, in order. Several bundle files may also be named
# explicitly, and they are processed as one stream.

set -e
cd "$(dirname "$0")"

if [ $# -gt 0 ]; then
    set -- "$@"
elif [ -f bundle.txt ]; then
    set -- bundle.txt
else
    # Numbered parts sort lexicographically because they are zero-padded.
    parts=$(ls bundle.part*.txt 2>/dev/null | sort) || true
    [ -n "$parts" ] || { echo "split.sh: no bundle.txt and no bundle.part*.txt" >&2; exit 1; }
    # shellcheck disable=SC2086
    set -- $parts
fi

for f; do
    [ -f "$f" ] || { echo "split.sh: not found: $f" >&2; exit 1; }
done

awk '
  function start(path) {
    n = split(path, parts, "/")
    if (n > 1) {
      dir = parts[1]
      for (i = 2; i < n; i++) dir = dir "/" parts[i]
      system("mkdir -p \"" dir "\"")
    }
    out = path
    printf "" > out
  }
  /^===FILE: .*===$/ {
    path = substr($0, 10, length($0) - 12)
    start(path)
    mode = "text"
    next
  }
  /^===FILE-B64: .*===$/ {
    path = substr($0, 14, length($0) - 16)
    start(path)
    mode = "b64"
    b64tmp = out ".b64.tmp"
    printf "" > b64tmp
    next
  }
  /^===END===$/ {
    if (mode == "b64") {
      close(b64tmp)
      system("base64 -d \"" b64tmp "\" > \"" out "\" && rm -f \"" b64tmp "\"")
    } else {
      close(out)
    }
    out = ""; mode = ""
    next
  }
  out {
    if (mode == "b64") print > b64tmp
    else print > out
  }
' "$@"

echo "Expanded $*"

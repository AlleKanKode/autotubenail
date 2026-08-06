#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "Brug: $0 <titel>" >&2
  exit 1
fi

cd "$(dirname "$0")"
OUTPUT=$(uv run thumbnail \
  --project tomatsource \
  --series tomat-source \
  --bg backgrounds/ts64-orig.png \
  --title "$1")

echo "$OUTPUT"
xdg-open "$(echo "$OUTPUT" | sed 's/Thumbnail saved: //')" &

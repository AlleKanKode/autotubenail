#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 2 ]; then
  echo "Brug: $0 <titel> <subtitel>" >&2
  exit 1
fi

cd "$(dirname "$0")"
OUTPUT=$(uv run thumbnail \
  --project tomatsource \
  --series tomat-source \
  --bg backgrounds/ts70-trae-raket.jpg \
  --text "main=$1" \
  --text "subtitle=$2")

echo "$OUTPUT"
xdg-open "$(echo "$OUTPUT" | sed 's/Thumbnail saved: //')" &

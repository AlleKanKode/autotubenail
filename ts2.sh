#!/usr/bin/env bash
set -euo pipefail

# Brug: ts2.sh <titel> <subtitel> [teknologi-ikoner...]
# Eksempel: ts2.sh "Python live" "Raket opsendelse" python javascript
#
# De valgfrie teknologi-ikoner indsættes i tech-pladsholderen (id "tech") i
# projects/tomatsource/config.json via --tech. Uden ikoner opfører scriptet
# sig præcis som ts.sh.

if [ "$#" -lt 2 ]; then
  echo "Brug: $0 <titel> <subtitel> [teknologi-ikoner...]" >&2
  echo "Eksempel: $0 'Python live' 'Raket' python javascript" >&2
  exit 1
fi

cd "$(dirname "$0")"

TITLE="$1"
SUBTITLE="$2"
shift 2

ARGS=(
  --project tomatsource
  --series tomat-source
  --bg backgrounds/ts72-liftoff.jpeg
  --text "main=$TITLE"
  --text "subtitle=$SUBTITLE"
)

if [ "$#" -gt 0 ]; then
  TECH_CSV=$(IFS=,; echo "$*")
  ARGS+=(--tech "tech=$TECH_CSV")
fi

OUTPUT=$(uv run thumbnail "${ARGS[@]}")
echo "$OUTPUT"
xdg-open "$(echo "$OUTPUT" | sed 's/Thumbnail saved: //')" &
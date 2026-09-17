#!/usr/bin/env bash
set -euo pipefail

# Brug: ts2.sh <titel> <subtitel> [ikon-navne...]
# Eksempel: ts2.sh "Python live" "Raket opsendelse" python tomat
#
# De valgfrie ikoner indsættes i icons-pladsholderen (id "icons") i
# projects/tomatsource/config.json via --icons. Navnene slås op i
# projects/tomatsource/icons/ (<navn>.svg eller <navn>.png). Uden ikoner
# opfører scriptet sig præcis som ts.sh.

if [ "$#" -lt 2 ]; then
  echo "Brug: $0 <titel> <subtitel> [ikon-navne...]" >&2
  echo "Eksempel: $0 'Python live' 'Raket' python tomat" >&2
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
  ICON_CSV=$(IFS=,; echo "$*")
  ARGS+=(--icons "$ICON_CSV")
fi

OUTPUT=$(uv run thumbnail "${ARGS[@]}")
echo "$OUTPUT"
xdg-open "$(echo "$OUTPUT" | sed 's/Thumbnail saved: //')" &
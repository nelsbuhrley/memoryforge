#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
LATEST_LOG="$PROJECT_DIR/logs/autopilot/latest.log"

if [[ ! -e "$LATEST_LOG" ]]; then
  echo "No autopilot log found yet at: $LATEST_LOG" >&2
  echo "Start autopilot first: ./tools/run_memoryforge_autopilot.sh" >&2
  exit 1
fi

exec tail -f "$LATEST_LOG"

#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

LOG_DIR="$PROJECT_DIR/logs/autopilot"
mkdir -p "$LOG_DIR"

TS="$(date +"%Y%m%d-%H%M%S")"
LOG_FILE="$LOG_DIR/autopilot-$TS.log"
LATEST_LINK="$LOG_DIR/latest.log"
ln -sfn "$LOG_FILE" "$LATEST_LINK"

echo "[launcher] Logging to $LOG_FILE"

python3 "$SCRIPT_DIR/claude_autopilot.py" \
  --project-dir "$PROJECT_DIR" \
  --start-time 12:01am \
  --start-tz America/Boise \
  --command claude \
  --permission-mode auto \
  --prompt $'First set to Use caveman ultra mode and ask minimal (if possible no) questions then\nPlease do the following:\n1) Review your memory\n2) Review and update PROGRESS.md\n3) Get back to work on building the memoryforge tool\n If you have compleated everything planed thus far for the project please begin planing stage 2 and then stop and wait for me to review the plans with you.' \
  --min-retry-minutes 3 \
  --availability-buffer-minutes 1 \
  2>&1 | tee -a "$LOG_FILE"

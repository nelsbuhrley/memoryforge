#!/usr/bin/env python3
"""Schedule and supervise Claude CLI runs for project workflows.

Features:
- Starts Claude at a scheduled local time (default: 12:30am in America/Denver).
- Launches with permission mode (default: auto).
- Sends a startup workflow prompt automatically.
- Watches stdout for usage-limit reset messages like:
  "You've hit your limit · resets 12am (America/Boise)"
- If that message appears, computes the next run time as the latest of:
  - now + 15 minutes
  - parsed reset time + 15 minutes
- Restarts Claude at that computed time.

This script intentionally does not attempt to auto-resolve permission prompts.
"""

from __future__ import annotations

import argparse
import re
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo

LIMIT_REGEX = re.compile(
    r"You['’]ve hit your limit.*?resets\s+([^()\n]+?)\s*\(([^)]+)\)",
    re.IGNORECASE,
)
RATE_LIMIT_MENU_REGEX = re.compile(r"What do you want to do\?", re.IGNORECASE)

# Track active child process so signal handlers can terminate it immediately.
ACTIVE_PROC: Optional[subprocess.Popen[str]] = None

DEFAULT_PROMPT = (
    "Please do the following:\n"
    "1) Review your memory\n"
    "2) Update PROGRESS.md\n"
    "3) Get back to work\n"
)


@dataclass
class LimitResetInfo:
    reset_datetime_utc: datetime
    source_text: str


def parse_time_token(token: str) -> tuple[int, int]:
    cleaned = token.strip().lower().replace(" ", "")
    formats = ["%I%p", "%I:%M%p"]
    for fmt in formats:
        try:
            parsed = datetime.strptime(cleaned, fmt)
            return parsed.hour, parsed.minute
        except ValueError:
            continue
    raise ValueError(f"Unsupported reset time token: {token!r}")


def parse_limit_reset_line(line: str, now_utc: datetime) -> Optional[LimitResetInfo]:
    match = LIMIT_REGEX.search(line)
    if not match:
        return None

    reset_token = match.group(1).strip()
    tz_name = match.group(2).strip()

    try:
        tz = ZoneInfo(tz_name)
        hour, minute = parse_time_token(reset_token)
    except Exception as exc:
        print(f"[autopilot] Could not parse reset message: {exc}", flush=True)
        return None

    now_local = now_utc.astimezone(tz)
    candidate = now_local.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if candidate <= now_local:
        candidate += timedelta(days=1)

    return LimitResetInfo(
        reset_datetime_utc=candidate.astimezone(timezone.utc),
        source_text=line.rstrip("\n"),
    )


def next_occurrence(now_utc: datetime, hour: int, minute: int, tz_name: str) -> datetime:
    tz = ZoneInfo(tz_name)
    now_local = now_utc.astimezone(tz)
    target_local = now_local.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target_local <= now_local:
        target_local += timedelta(days=1)
    return target_local.astimezone(timezone.utc)


def sleep_until(target_utc: datetime) -> None:
    while True:
        now = datetime.now(timezone.utc)
        remaining = (target_utc - now).total_seconds()
        if remaining <= 0:
            return
        time.sleep(min(remaining, 30))


def format_dt(dt: datetime, tz_name: str) -> str:
    tz = ZoneInfo(tz_name)
    local = dt.astimezone(tz)
    return local.strftime("%Y-%m-%d %H:%M:%S %Z")


def start_claude_process(
    project_dir: Path,
    command: str,
    permission_mode: str,
    prompt: str,
    print_mode: bool,
) -> subprocess.Popen[str]:
    cmd = [command, "--permission-mode", permission_mode]
    if print_mode:
        cmd.append("--print")
        cmd.append(prompt)
    print(f"[autopilot] Starting: {' '.join(cmd)} in {project_dir}", flush=True)
    return subprocess.Popen(
        cmd,
        cwd=str(project_dir),
        stdin=subprocess.PIPE if not print_mode else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )


def send_startup_prompt(proc: subprocess.Popen[str], prompt: str) -> None:
    if proc.stdin is None:
        return
    proc.stdin.write(prompt)
    if not prompt.endswith("\n"):
        proc.stdin.write("\n")
    proc.stdin.flush()
    print("[autopilot] Sent startup workflow prompt.", flush=True)


def monitor_once(
    project_dir: Path,
    command: str,
    permission_mode: str,
    prompt: str,
    print_mode: bool,
    min_retry_minutes: int,
    availability_buffer_minutes: int,
) -> Optional[datetime]:
    global ACTIVE_PROC
    proc = start_claude_process(project_dir, command, permission_mode, prompt, print_mode)
    ACTIVE_PROC = proc
    if not print_mode:
        send_startup_prompt(proc, prompt)

    try:
        assert proc.stdout is not None
        for line in proc.stdout:
            print(line, end="")

            # Safety rule: if interactive rate-limit options appear, always select "1".
            if RATE_LIMIT_MENU_REGEX.search(line):
                if proc.stdin is not None:
                    proc.stdin.write("1\n")
                    proc.stdin.flush()
                    print("[autopilot] Rate-limit menu detected. Selected option 1 (wait for reset).", flush=True)
                else:
                    print(
                        "[autopilot] Rate-limit menu text detected in non-interactive mode; no paid option will be selected.",
                        flush=True,
                    )

            reset_info = parse_limit_reset_line(line, datetime.now(timezone.utc))
            if reset_info is None:
                continue

            now_utc = datetime.now(timezone.utc)
            earliest_retry = now_utc + timedelta(minutes=min_retry_minutes)
            available_retry = reset_info.reset_datetime_utc + timedelta(minutes=availability_buffer_minutes)
            restart_at = max(earliest_retry, available_retry)

            print(
                "[autopilot] Usage limit detected. "
                f"Reset line: {reset_info.source_text}\n"
                f"[autopilot] Will restart at {restart_at.isoformat()} UTC",
                flush=True,
            )

            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
            return restart_at

        code = proc.wait()
        print(f"[autopilot] Claude exited with code {code}.", flush=True)
        return None

    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        ACTIVE_PROC = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Claude CLI scheduler and usage-limit watchdog")
    parser.add_argument(
        "--project-dir",
        default=".",
        help="Folder where Claude should start (default: current directory)",
    )
    parser.add_argument(
        "--start-time",
        default="12:30am",
        help="Local start time in --start-tz (HH:MM 24h or H:MMam/pm)",
    )
    parser.add_argument(
        "--start-tz",
        default="America/Denver",
        help="IANA timezone for --start-time (default: America/Denver)",
    )
    parser.add_argument(
        "--command",
        default="claude",
        help="Claude command to execute (default: claude)",
    )
    parser.add_argument(
        "--permission-mode",
        default="auto",
        help="Permission mode passed to Claude (default: auto)",
    )
    parser.add_argument(
        "--prompt",
        default=DEFAULT_PROMPT,
        help="Prompt sent immediately after Claude starts",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Use interactive Claude mode instead of --print (can block in non-TTY automation)",
    )
    parser.add_argument(
        "--min-retry-minutes",
        type=int,
        default=15,
        help="Minimum delay from now before any restart (default: 15)",
    )
    parser.add_argument(
        "--availability-buffer-minutes",
        type=int,
        default=15,
        help="Delay after parsed reset time before restart (default: 15)",
    )
    return parser.parse_args()


def parse_start_time(start_time: str) -> tuple[int, int]:
    token = start_time.strip().lower().replace(" ", "")

    # Accept both 24-hour HH:MM and 12-hour am/pm inputs.
    for fmt in ("%H:%M", "%I:%M%p"):
        try:
            parsed = datetime.strptime(token, fmt)
            return parsed.hour, parsed.minute
        except ValueError:
            continue

    raise ValueError("--start-time must be HH:MM (24h) or H:MMam/pm (e.g., 12:30am)")


def main() -> int:
    args = parse_args()

    project_dir = Path(args.project_dir).resolve()
    if not project_dir.exists() or not project_dir.is_dir():
        print(f"[autopilot] Invalid --project-dir: {project_dir}", file=sys.stderr)
        return 2

    try:
        ZoneInfo(args.start_tz)
    except Exception:
        print(f"[autopilot] Invalid timezone: {args.start_tz}", file=sys.stderr)
        return 2

    try:
        start_hour, start_minute = parse_start_time(args.start_time)
    except ValueError as exc:
        print(f"[autopilot] {exc}", file=sys.stderr)
        return 2

    stop_requested = False
    print_mode = not args.interactive

    if print_mode:
        print("[autopilot] Using non-interactive Claude --print mode.", flush=True)
    else:
        print("[autopilot] Using interactive Claude mode.", flush=True)

    def _handle_signal(_signum: int, _frame: object) -> None:
        nonlocal stop_requested
        global ACTIVE_PROC
        stop_requested = True
        print("\n[autopilot] Stop requested. Exiting now.", flush=True)

        # Ensure Ctrl+C promptly stops the child Claude process too.
        if ACTIVE_PROC is not None and ACTIVE_PROC.poll() is None:
            try:
                ACTIVE_PROC.terminate()
                ACTIVE_PROC.wait(timeout=3)
            except Exception:
                try:
                    ACTIVE_PROC.kill()
                except Exception:
                    pass

        raise KeyboardInterrupt()

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    first_run_at = next_occurrence(datetime.now(timezone.utc), start_hour, start_minute, args.start_tz)
    print(
        "[autopilot] First scheduled run at "
        f"{format_dt(first_run_at, args.start_tz)} ({args.start_tz})",
        flush=True,
    )

    current_target = first_run_at

    try:
        while not stop_requested:
            sleep_until(current_target)
            if stop_requested:
                break

            restart_at = monitor_once(
                project_dir=project_dir,
                command=args.command,
                permission_mode=args.permission_mode,
                prompt=args.prompt,
                print_mode=print_mode,
                min_retry_minutes=args.min_retry_minutes,
                availability_buffer_minutes=args.availability_buffer_minutes,
            )

            if stop_requested:
                break

            if restart_at is None:
                # If Claude exits normally, wait until next scheduled daily start.
                current_target = next_occurrence(datetime.now(timezone.utc), start_hour, start_minute, args.start_tz)
                print(
                    "[autopilot] No usage-limit message observed. "
                    f"Next daily run at {format_dt(current_target, args.start_tz)} ({args.start_tz})",
                    flush=True,
                )
            else:
                current_target = restart_at
                print(
                    f"[autopilot] Rearmed for {format_dt(current_target, args.start_tz)} ({args.start_tz})",
                    flush=True,
                )
    except KeyboardInterrupt:
        print("[autopilot] Interrupted. Exiting.", flush=True)
        return 130

    print("[autopilot] Exiting.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

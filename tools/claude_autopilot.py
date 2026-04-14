#!/usr/bin/env python3
"""Schedule and supervise Claude CLI runs for project workflows with enhanced logging.

Features:
- Comprehensive environment and project diagnostics at startup
- Timestamps on all log messages
- Project structure inspection
- Detailed configuration logging
- Real-time Claude process monitoring
- Starts Claude at a scheduled local time (default: 12:30am in America/Denver).
- Launches with permission mode (default: auto).
- Sends a startup workflow prompt automatically.
- Watches stdout for usage-limit reset messages
- Restarts Claude when limits are hit with detailed tracking
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
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
    r"You['']ve hit your limit.*?resets\s+([^()\n]+?)\s*\(([^)]+)\)",
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


def get_timestamp() -> str:
    """Return current timestamp in ISO format."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def log(msg: str, level: str = "INFO") -> None:
    """Log with timestamp."""
    timestamp = get_timestamp()
    print(f"[{timestamp}] [{level:7s}] {msg}", flush=True)


def log_section(title: str) -> None:
    """Log a section header."""
    print(f"\n{'=' * 80}", flush=True)
    log(f"▶ {title}")
    print(f"{'=' * 80}\n", flush=True)


def diagnose_environment(project_dir: Path) -> None:
    """Log comprehensive environment and project diagnostics."""
    log_section("ENVIRONMENT DIAGNOSTICS")

    # System info
    log(f"Python: {sys.version}")
    log(f"Platform: {sys.platform}")
    log(f"Working Directory: {Path.cwd()}")
    log(f"Project Directory: {project_dir}")
    log(f"Project exists: {project_dir.exists()}")
    
    # Claude command check
    claude_path = shutil.which("claude")
    if claude_path:
        log(f"Claude command found at: {claude_path}")
    else:
        log("Claude command NOT FOUND in PATH", level="WARNING")

    # Environment variables (non-sensitive)
    log("\nRelevant environment variables:")
    env_vars_to_check = [
        "PATH", "HOME", "USER", "SHELL", "LANG",
        "ANTHROPIC_HOME", "CLAUDE_HOME",
        "PROJECT_HOME", "WORKSPACE"
    ]
    for var in env_vars_to_check:
        val = os.environ.get(var)
        if val:
            # Truncate long paths for readability
            display_val = val if len(val) < 80 else val[:77] + "..."
            log(f"  {var}: {display_val}")

    # Project structure
    log_section("PROJECT STRUCTURE")
    try:
        items = sorted(project_dir.iterdir())
        log(f"Found {len(items)} items in {project_dir.name}/")
        
        # Categorize items
        dirs = [item for item in items if item.is_dir() and not item.name.startswith('.')]
        files = [item for item in items if item.is_file() and not item.name.startswith('.')]
        
        if dirs:
            log("Directories:")
            for d in sorted(dirs):
                item_count = len(list(d.iterdir()))
                log(f"  📁 {d.name}/ ({item_count} items)")
        
        if files:
            log("Files:")
            for f in sorted(files):
                size_kb = f.stat().st_size / 1024
                log(f"  📄 {f.name} ({size_kb:.1f} KB)")
    except Exception as e:
        log(f"Error reading project directory: {e}", level="ERROR")

    # Key files check
    log_section("KEY FILES CHECK")
    key_files = [
        "PROGRESS.md",
        "pyproject.toml",
        ".git/config",
        "README.md",
    ]
    for key_file in key_files:
        path = project_dir / key_file
        exists = "✓" if path.exists() else "✗"
        log(f"  {exists} {key_file}")


def diagnose_command(command: str, permission_mode: str, print_mode: bool, prompt: str) -> None:
    """Log the command that will be executed."""
    log_section("COMMAND CONFIGURATION")
    
    cmd_parts = [command, "--permission-mode", permission_mode]
    if print_mode:
        cmd_parts.extend(["--print", "[prompt will be piped]"])
    
    log("Full command:")
    log(f"  {' '.join(cmd_parts)}")
    
    log("\nConfiguration:")
    log(f"  Command: {command}")
    log(f"  Permission mode: {permission_mode}")
    log(f"  Mode: {'Non-interactive (--print)' if print_mode else 'Interactive (stdin)'}")
    log(f"  Prompt length: {len(prompt)} chars")
    log(f"  Prompt preview: {prompt[:100].splitlines()[0]!r}...")


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
        log(f"Could not parse reset message: {exc}", level="WARNING")
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


def format_dt(dt: datetime, tz_name: str) -> str:
    tz = ZoneInfo(tz_name)
    local = dt.astimezone(tz)
    return local.strftime("%Y-%m-%d %H:%M:%S %Z")


def sleep_until(target_utc: datetime, tz_name: str) -> None:
    """Sleep until target time, logging progress at adaptive intervals."""
    last_log_time = 0.0
    
    while True:
        now = datetime.now(timezone.utc)
        remaining = (target_utc - now).total_seconds()
        if remaining <= 0:
            log("Scheduled time reached, starting Claude now")
            return
        
        # Determine check interval based on remaining time
        if remaining > 7200:  # > 2 hours
            check_interval = 3600  # Every hour
        elif remaining > 3600:  # > 1 hour
            check_interval = 1800  # Every 30 min
        elif remaining > 1200:  # > 20 minutes
            check_interval = 600   # Every 10 min
        elif remaining > 300:    # > 5 minutes
            check_interval = 60    # Every min
        else:                      # < 1 minute (actually < 5 min)
            check_interval = 30    # Every 30 sec
        
        # Log if enough time has passed since last log
        if time.time() - last_log_time >= check_interval - 1:  # -1 for safety margin
            hours = int(remaining) // 3600
            mins = (int(remaining) % 3600) // 60
            secs = int(remaining) % 60
            
            if hours > 0:
                log(f"Waiting {hours}h {mins}m {secs}s for next run at {format_dt(target_utc, tz_name)}")
            elif mins > 0:
                log(f"Waiting {mins}m {secs}s for next run at {format_dt(target_utc, tz_name)}")
            else:
                log(f"Waiting {secs}s for next run at {format_dt(target_utc, tz_name)}")
            
            last_log_time = time.time()
        
        time.sleep(min(remaining, 10))


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
    
    log(f"Starting Claude process in: {project_dir}")
    log(f"Full command: {' '.join(cmd)}")
    
    try:
        proc = subprocess.Popen(
            cmd,
            cwd=str(project_dir),
            stdin=subprocess.PIPE if not print_mode else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        log(f"✓ Claude process started with PID {proc.pid}")
        return proc
    except FileNotFoundError:
        log(f"✗ Command not found: {command}", level="ERROR")
        log(f"  Tried to execute from: {project_dir}", level="ERROR")
        log(f"  Make sure '{command}' is installed and in PATH", level="ERROR")
        raise
    except Exception as e:
        log(f"✗ Failed to start Claude process: {e}", level="ERROR")
        raise


def send_startup_prompt(proc: subprocess.Popen[str], prompt: str) -> None:
    if proc.stdin is None:
        return
    proc.stdin.write(prompt)
    if not prompt.endswith("\n"):
        proc.stdin.write("\n")
    proc.stdin.flush()
    log(f"Sent startup prompt ({len(prompt)} chars)")


def monitor_once(
    project_dir: Path,
    command: str,
    permission_mode: str,
    prompt: str,
    print_mode: bool,
    min_retry_minutes: int,
    availability_buffer_minutes: int,
    tz_name: str,
) -> Optional[datetime]:
    """Monitor a single Claude session, return restart time if limit hit."""
    global ACTIVE_PROC
    
    log_section("CLAUDE SESSION START")
    log(f"Started at: {get_timestamp()}")
    
    proc = start_claude_process(project_dir, command, permission_mode, prompt, print_mode)
    ACTIVE_PROC = proc
    if not print_mode:
        send_startup_prompt(proc, prompt)

    log("Waiting for Claude output...")
    log_separator = "─" * 80
    print(f"\n{log_separator}\n", end="")
    
    line_count = 0
    startup_logged = False
    
    try:
        assert proc.stdout is not None
        for line in proc.stdout:
            line_count += 1
            
            # Log startup info on first output
            if not startup_logged:
                log(f"✓ Claude is responding (first output at line {line_count})", level="INFO")
                startup_logged = True
            
            print(line, end="")

            # Safety rule: if interactive rate-limit options appear, always select "1".
            if RATE_LIMIT_MENU_REGEX.search(line):
                if proc.stdin is not None:
                    proc.stdin.write("1\n")
                    proc.stdin.flush()
                    log("Rate-limit menu detected. Selected option 1 (wait for reset).", level="WARN")
                else:
                    log("Rate-limit menu detected but in non-interactive mode", level="WARN")

            reset_info = parse_limit_reset_line(line, datetime.now(timezone.utc))
            if reset_info is None:
                continue

            log_section("USAGE LIMIT DETECTED")
            log(f"Detected at: {get_timestamp()}")
            log(f"Reset message: {reset_info.source_text}")

            now_utc = datetime.now(timezone.utc)
            earliest_retry = now_utc + timedelta(minutes=min_retry_minutes)
            available_retry = reset_info.reset_datetime_utc + timedelta(minutes=availability_buffer_minutes)
            restart_at = max(earliest_retry, available_retry)

            log(f"Parsed reset time: {format_dt(reset_info.reset_datetime_utc, tz_name)}")
            log(f"Earliest retry (now + {min_retry_minutes}m): {format_dt(earliest_retry, tz_name)}")
            log(f"Available retry (+{availability_buffer_minutes}m buffer): {format_dt(available_retry, tz_name)}")
            log(f"Will restart at: {format_dt(restart_at, tz_name)}")
            log(f"Processed {line_count} output lines")

            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
            return restart_at

        code = proc.wait()
        
        log_section("CLAUDE SESSION ENDED")
        log(f"Exit code: {code}")
        log(f"Output lines: {line_count}")
        log(f"Ended at: {get_timestamp()}")
        
        if code == 0:
            log("Claude exited cleanly", level="INFO")
        elif code == 130:
            log("Claude interrupted by user (Ctrl+C)", level="INFO")
        else:
            log(f"Claude exited with code {code}", level="WARNING")
        
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
    parser = argparse.ArgumentParser(
        description="Claude CLI scheduler with enhanced diagnostics and monitoring"
    )
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
        help="Use interactive Claude mode instead of --print",
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
    parser.add_argument(
        "--run-now",
        action="store_true",
        default=True,
        help="Start Claude immediately on first run instead of waiting for scheduled time (default: true)",
    )
    parser.add_argument(
        "--no-run-now",
        action="store_false",
        dest="run_now",
        help="Disable immediate start, wait until scheduled time (opposite of --run-now)",
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
        log(f"Invalid --project-dir: {project_dir}", level="ERROR")
        return 2

    try:
        ZoneInfo(args.start_tz)
    except Exception:
        log(f"Invalid timezone: {args.start_tz}", level="ERROR")
        return 2

    try:
        start_hour, start_minute = parse_start_time(args.start_time)
    except ValueError as exc:
        log(f"Invalid start time: {exc}", level="ERROR")
        return 2

    # Run comprehensive diagnostics at startup
    log_section("AUTOPILOT STARTING")
    log(f"Timestamp: {get_timestamp()}")
    
    diagnose_environment(project_dir)
    diagnose_command(args.command, args.permission_mode, not args.interactive, args.prompt)

    stop_requested = False
    print_mode = not args.interactive

    if print_mode:
        log("Mode: Non-interactive (--print)")
    else:
        log("Mode: Interactive (stdin)")

    def _handle_signal(_signum: int, _frame: object) -> None:
        nonlocal stop_requested
        global ACTIVE_PROC
        stop_requested = True
        log("\n⚠️  Stop requested via signal. Shutting down...", level="WARN")

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

    # Determine first run timing
    if args.run_now:
        current_target = datetime.now(timezone.utc)  # Start immediately
        scheduled_time = next_occurrence(datetime.now(timezone.utc), start_hour, start_minute, args.start_tz)
        log_section("SCHEDULE")
        log(f"Starting Claude immediately (--run-now enabled)")
        log(f"Scheduled time for subsequent runs: {format_dt(scheduled_time, args.start_tz)}")
        log(f"Timezone: {args.start_tz}")
    else:
        current_target = next_occurrence(datetime.now(timezone.utc), start_hour, start_minute, args.start_tz)
        log_section("SCHEDULE")
        log(f"First run scheduled at: {format_dt(current_target, args.start_tz)}")
        log(f"Timezone: {args.start_tz}")
    run_number = 0

    try:
        while not stop_requested:
            sleep_until(current_target, args.start_tz)
            if stop_requested:
                break

            run_number += 1
            log_section(f"RUN #{run_number}")

            restart_at = monitor_once(
                project_dir=project_dir,
                command=args.command,
                permission_mode=args.permission_mode,
                prompt=args.prompt,
                print_mode=print_mode,
                min_retry_minutes=args.min_retry_minutes,
                availability_buffer_minutes=args.availability_buffer_minutes,
                tz_name=args.start_tz,
            )

            if stop_requested:
                break

            if restart_at is None:
                # If Claude exits normally, wait until next scheduled daily start.
                current_target = next_occurrence(datetime.now(timezone.utc), start_hour, start_minute, args.start_tz)
                log_section("NEXT SCHEDULED RUN")
                log(f"Claude exited normally")
                log(f"Next run at: {format_dt(current_target, args.start_tz)}")
            else:
                current_target = restart_at
                log_section("REARMED FOR RESTART")
                log(f"Will restart at: {format_dt(current_target, args.start_tz)}")

    except KeyboardInterrupt:
        log("Interrupted by user", level="INFO")
        return 130

    log_section("AUTOPILOT SHUTDOWN")
    log(f"Exiting gracefully at: {get_timestamp()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

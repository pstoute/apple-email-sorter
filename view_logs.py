#!/usr/bin/env python3
"""
View and tail email sorter logs
"""
import argparse
import subprocess
from pathlib import Path
from config import LOG_FILE, LOG_DIR


def view_logs(tail: bool = False, lines: int = 50, follow: bool = False, grep: str = None):
    """
    View log files

    Args:
        tail: Show only last N lines
        lines: Number of lines to show (for tail)
        follow: Follow log file (like tail -f)
        grep: Filter logs by pattern
    """
    if not LOG_FILE.exists():
        print(f"Log file not found: {LOG_FILE}")
        print("Run the email sorter first to generate logs.")
        return

    print(f"📄 Log file: {LOG_FILE}")
    print(f"📊 Size: {LOG_FILE.stat().st_size:,} bytes")
    print("=" * 70)
    print()

    # Build command
    if follow:
        cmd = ["tail", "-f", str(LOG_FILE)]
        if grep:
            cmd = cmd + ["|", "grep", "--color=auto", grep]
        print(f"Following log file (Ctrl+C to stop)...")
        print()
    elif tail:
        cmd = ["tail", f"-n{lines}", str(LOG_FILE)]
    else:
        cmd = ["cat", str(LOG_FILE)]

    # Add grep filter if specified
    if grep and not follow:
        cmd_str = " ".join(cmd) + f" | grep --color=auto '{grep}'"
        subprocess.run(cmd_str, shell=True)
    else:
        if follow:
            # For follow mode, need shell=True to handle pipe
            cmd_str = " ".join(cmd)
            subprocess.run(cmd_str, shell=True)
        else:
            subprocess.run(cmd)


def list_log_files():
    """List all log files"""
    if not LOG_DIR.exists():
        print(f"Log directory not found: {LOG_DIR}")
        return

    log_files = sorted(LOG_DIR.glob("*.log*"))

    if not log_files:
        print(f"No log files found in {LOG_DIR}")
        return

    print(f"📁 Log directory: {LOG_DIR}")
    print("=" * 70)
    print()

    total_size = 0
    for log_file in log_files:
        size = log_file.stat().st_size
        total_size += size
        print(f"  {log_file.name:40} {size:>10,} bytes")

    print()
    print(f"Total: {len(log_files)} files, {total_size:,} bytes")


def clear_logs():
    """Clear all log files"""
    if not LOG_DIR.exists():
        print(f"Log directory not found: {LOG_DIR}")
        return

    log_files = list(LOG_DIR.glob("*.log*"))

    if not log_files:
        print("No log files to clear")
        return

    print(f"Found {len(log_files)} log file(s):")
    for log_file in log_files:
        print(f"  - {log_file.name}")

    response = input("\nDelete all log files? (yes/no): ").strip().lower()

    if response == "yes":
        for log_file in log_files:
            log_file.unlink()
            print(f"✓ Deleted {log_file.name}")
        print(f"\n✓ Cleared {len(log_files)} log file(s)")
    else:
        print("Cancelled")


def main():
    parser = argparse.ArgumentParser(
        description="View email sorter logs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # View full log
  %(prog)s --tail             # View last 50 lines
  %(prog)s --tail -n 100      # View last 100 lines
  %(prog)s --follow           # Follow log in real-time
  %(prog)s --grep ERROR       # Show only ERROR lines
  %(prog)s --list             # List all log files
  %(prog)s --clear            # Clear all log files
        """
    )

    parser.add_argument(
        "--tail",
        action="store_true",
        help="Show only last N lines (default: 50)"
    )
    parser.add_argument(
        "-n", "--lines",
        type=int,
        default=50,
        help="Number of lines to show with --tail (default: 50)"
    )
    parser.add_argument(
        "-f", "--follow",
        action="store_true",
        help="Follow log file in real-time (like tail -f)"
    )
    parser.add_argument(
        "--grep",
        type=str,
        help="Filter logs by pattern (e.g., ERROR, WARNING, summary)"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all log files"
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear all log files"
    )

    args = parser.parse_args()

    if args.list:
        list_log_files()
    elif args.clear:
        clear_logs()
    else:
        view_logs(
            tail=args.tail,
            lines=args.lines,
            follow=args.follow,
            grep=args.grep
        )


if __name__ == "__main__":
    main()

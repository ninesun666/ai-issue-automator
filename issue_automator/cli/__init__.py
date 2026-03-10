"""
issue_automator.cli - Command line interface for AI Harness.

This module provides CLI commands for running the automation service.
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Optional

from issue_automator.cli.automation import run_automation_server

__all__ = ["main", "run_automation_server"]


def setup_logging(verbose: bool = False) -> None:
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="ai-harness",
        description="AI Harness - Automated development pipeline",
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Automation server command
    auto_parser = subparsers.add_parser(
        "automation",
        help="Run the automation server",
    )
    auto_parser.add_argument(
        "action",
        choices=["start", "status"],
        help="Action to perform",
    )
    auto_parser.add_argument(
        "-c", "--config",
        type=str,
        help="Path to configuration file",
    )
    auto_parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Webhook server port (default: 8080)",
    )
    auto_parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Webhook server host (default: 0.0.0.0)",
    )
    auto_parser.add_argument(
        "--work-dir",
        type=str,
        default="./repos",
        help="Working directory for repositories",
    )
    auto_parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    # Parse arguments
    args = parser.parse_args()

    # Setup logging
    setup_logging(verbose=getattr(args, "verbose", False))

    # Handle commands
    if args.command == "automation":
        return run_automation_server(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
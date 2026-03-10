"""
Automation CLI commands.

This module provides the CLI interface for running the automation
server and managing the automation pipeline.
"""

import json
import logging
import os
import signal
import sys
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def run_automation_server(args) -> int:
    """
    Run the automation server.

    Args:
        args: Parsed argparse arguments

    Returns:
        Exit code
    """
    if args.action == "status":
        return _show_status(args)
    elif args.action == "start":
        return _start_server(args)
    else:
        logger.error(f"Unknown action: {args.action}")
        return 1


def _start_server(args) -> int:
    """Start the webhook server and scheduler."""
    # Load configuration
    config = _load_config(args.config)

    # Get required settings
    github_token = os.environ.get("GITHUB_TOKEN") or config.get("github", {}).get("token")
    webhook_secret = os.environ.get("GITHUB_WEBHOOK_SECRET") or config.get("webhook", {}).get("secret")

    if not github_token:
        logger.error("GitHub token is required. Set GITHUB_TOKEN environment variable or configure in config file.")
        return 1

    if not webhook_secret:
        logger.warning("No webhook secret configured. Signature verification will fail.")

    # Get settings from args or config
    port = args.port or config.get("webhook", {}).get("port", 8080)
    host = args.host or config.get("webhook", {}).get("host", "0.0.0.0")
    work_dir = Path(args.work_dir or config.get("work_dir", "./repos"))

    logger.info(f"Starting automation server on {host}:{port}")
    logger.info(f"Working directory: {work_dir}")

    # Initialize components
    from issue_automator.webhook.server import WebhookServer
    from issue_automator.core.pipeline import AutomationPipeline
    from issue_automator.core.task_manager import TaskQueue
    from issue_automator.core.scheduler import TaskScheduler

    # Create task queue
    task_queue = TaskQueue()

    # Create pipeline
    pipeline = AutomationPipeline(
        work_dir=work_dir,
        github_token=github_token,
        webhook_secret=webhook_secret,
        default_reviewers=config.get("workflow", {}).get("default_reviewers", []),
    )

    # Create scheduler
    scheduler = TaskScheduler(task_queue, pipeline)

    # Create webhook server
    server = WebhookServer(
        secret=webhook_secret or "",
        host=host,
        port=port,
    )

    # Register issue handler
    def on_issue_created(issue_payload):
        """Handle new issue creation."""
        logger.info(f"New issue received: #{issue_payload.number} in {issue_payload.repository_full_name}")
        
        # Add to task queue
        task_queue.add_task(
            issue_number=issue_payload.number,
            repo=issue_payload.repository_full_name,
            title=issue_payload.title,
            issue_data={
                "issue": {
                    "number": issue_payload.number,
                    "title": issue_payload.title,
                    "body": issue_payload.body,
                    "html_url": issue_payload.html_url,
                    "labels": [{"name": label} for label in issue_payload.labels],
                    "state": issue_payload.state,
                },
                "repository": {
                    "name": issue_payload.repository,
                    "full_name": issue_payload.repository_full_name,
                },
                "sender": {
                    "login": issue_payload.sender,
                },
                "action": "opened",
            },
        )

    server.on_issue_created(on_issue_created)

    # Setup signal handlers
    def signal_handler(signum, frame):
        """Handle shutdown signals."""
        logger.info("Shutting down...")
        scheduler.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start scheduler
    scheduler.start()
    logger.info("Task scheduler started")

    # Start webhook server (blocking)
    logger.info(f"Webhook server listening on http://{host}:{port}/webhook")
    logger.info("Ready to receive GitHub webhooks!")

    try:
        server.start()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
        scheduler.stop()

    return 0


def _show_status(args) -> int:
    """Show automation server status."""
    # For now, just show configuration status
    config = _load_config(args.config)

    print("AI Harness Automation Status")
    print("=" * 40)

    # Check GitHub token
    github_token = os.environ.get("GITHUB_TOKEN")
    if github_token:
        print("GitHub Token: Configured (from environment)")
    elif config.get("github", {}).get("token"):
        print("GitHub Token: Configured (from config)")
    else:
        print("GitHub Token: NOT CONFIGURED")

    # Check webhook secret
    webhook_secret = os.environ.get("GITHUB_WEBHOOK_SECRET")
    if webhook_secret:
        print("Webhook Secret: Configured (from environment)")
    elif config.get("webhook", {}).get("secret"):
        print("Webhook Secret: Configured (from config)")
    else:
        print("Webhook Secret: NOT CONFIGURED")

    # Show configured projects
    projects = config.get("projects", {})
    if projects:
        print(f"\nConfigured Projects: {len(projects)}")
        for name, project in projects.items():
            print(f"  - {name}: {project.get('repo', 'N/A')}")
    else:
        print("\nNo projects configured")

    print("\nConfiguration file:", args.config or "Not specified")

    return 0


def _load_config(config_path: Optional[str]) -> Dict[str, Any]:
    """Load configuration from file."""
    if not config_path:
        # Try default locations
        default_paths = [
            Path.cwd() / "ai-harness.config.json",
            Path.cwd() / ".ai-harness" / "config.json",
            Path.home() / ".ai-harness" / "config.json",
        ]
        for path in default_paths:
            if path.exists():
                config_path = str(path)
                break

    if not config_path:
        return {}

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Failed to load config from {config_path}: {e}")
        return {}

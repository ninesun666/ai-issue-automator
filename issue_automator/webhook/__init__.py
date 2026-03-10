"""
Webhook module for receiving GitHub events.

This module provides a Flask-based webhook server that handles
GitHub webhook events and triggers the automation pipeline.
"""

from issue_automator.webhook.server import WebhookServer
from issue_automator.webbook.handlers import GitHubEventHandler
from issue_automator.webhook.signature import verify_github_signature

__all__ = [
    "WebhookServer",
    "GitHubEventHandler",
    "verify_github_signature",
]

"""
Notification module for GitHub API interactions.

This module provides GitHub API client and notification utilities
for creating issues, pull requests, and updating statuses.
"""

from issue_automator.notification.github_client import GitHubClient
from issue_automator.notification.notifier import Notifier

__all__ = [
    "GitHubClient",
    "Notifier",
]

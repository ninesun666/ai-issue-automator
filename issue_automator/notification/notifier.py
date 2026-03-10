"""
Notification utilities for automation pipeline.

This module provides high-level notification functions for the
automation workflow, including failure notifications and status updates.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

from issue_automator.notification.github_client import GitHubClient

logger = logging.getLogger(__name__)


class NotificationType(Enum):
    """Types of notifications."""
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    PR_CREATED = "pr_created"
    REVIEW_REQUESTED = "review_requested"


@dataclass
class NotificationContext:
    """Context for notifications."""
    repo: str
    issue_number: int
    branch_name: Optional[str] = None
    pr_number: Optional[int] = None
    error_message: Optional[str] = None
    task_description: Optional[str] = None


class Notifier:
    """
    Notification manager for automation pipeline.

    This class handles all notifications related to the automation
    workflow, including creating issues for failures and updating
    existing issues with progress.

    Example:
        >>> notifier = Notifier(github_client)
        >>> notifier.notify_failure(ctx, "Task failed: timeout")
    """

    def __init__(self, github_client: GitHubClient):
        """
        Initialize the notifier.

        Args:
            github_client: GitHubClient instance for API operations
        """
        self.client = github_client

    def notify_task_started(self, ctx: NotificationContext) -> None:
        """
        Notify that a task has started processing.

        Args:
            ctx: Notification context
        """
        message = f"🤖 **AI Automation Started**\n\n"
        message += f"Processing this issue automatically.\n"
        if ctx.branch_name:
            message += f"- **Branch**: `{ctx.branch_name}`\n"
        message += f"\n_I will update this issue with progress._"

        self.client.add_issue_comment(
            repo=ctx.repo,
            issue_number=ctx.issue_number,
            comment=message,
        )
        logger.info(f"Notified task start for issue #{ctx.issue_number}")

    def notify_task_completed(
        self,
        ctx: NotificationContext,
        pr_url: Optional[str] = None,
    ) -> None:
        """
        Notify that a task has completed successfully.

        Args:
            ctx: Notification context
            pr_url: URL of the created pull request
        """
        message = f"✅ **AI Automation Completed**\n\n"
        if pr_url:
            message += f"Pull request created: {pr_url}\n\n"
        message += "Please review and merge when ready."

        self.client.add_issue_comment(
            repo=ctx.repo,
            issue_number=ctx.issue_number,
            comment=message,
        )
        logger.info(f"Notified task completion for issue #{ctx.issue_number}")

    def notify_failure(
        self,
        ctx: NotificationContext,
        error_message: str,
        create_issue: bool = True,
    ) -> Optional[int]:
        """
        Notify that a task has failed.

        Args:
            ctx: Notification context
            error_message: Error description
            create_issue: Whether to create a new issue for manual intervention

        Returns:
            Issue number if a new issue was created, None otherwise
        """
        # Add comment to original issue
        message = f"❌ **AI Automation Failed**\n\n"
        message += f"Error: {error_message}\n\n"
        message += "Manual intervention may be required."

        self.client.add_issue_comment(
            repo=ctx.repo,
            issue_number=ctx.issue_number,
            comment=message,
        )

        # Create new issue for manual intervention
        if create_issue:
            new_issue = self.client.create_issue(
                repo=ctx.repo,
                title=f"[Manual Review Required] Failed to process issue #{ctx.issue_number}",
                body=self._build_failure_issue_body(ctx, error_message),
                labels=["ai-automation-failed", "needs-review"],
            )
            logger.info(f"Created issue #{new_issue.number} for manual review")
            return new_issue.number

        return None

    def notify_pr_created(
        self,
        ctx: NotificationContext,
        pr_number: int,
        pr_url: str,
    ) -> None:
        """
        Notify that a pull request has been created.

        Args:
            ctx: Notification context
            pr_number: Pull request number
            pr_url: Pull request URL
        """
        message = f"🔀 **Pull Request Created**\n\n"
        message += f"PR #{pr_number}: {pr_url}\n\n"
        message += "Ready for review."

        self.client.add_issue_comment(
            repo=ctx.repo,
            issue_number=ctx.issue_number,
            comment=message,
        )
        logger.info(f"Notified PR #{pr_number} creation for issue #{ctx.issue_number}")

    def request_review(
        self,
        ctx: NotificationContext,
        pr_number: int,
        reviewers: List[str],
    ) -> None:
        """
        Request review for a pull request.

        Args:
            ctx: Notification context
            pr_number: Pull request number
            reviewers: List of reviewer usernames
        """
        self.client.request_review(
            repo=ctx.repo,
            pr_number=pr_number,
            reviewers=reviewers,
        )

        # Add comment to issue
        message = f"👀 **Review Requested**\n\n"
        message += f"Reviewers: {', '.join(f'@{r}' for r in reviewers)}\n"
        message += f"PR #{pr_number} is ready for review."

        self.client.add_issue_comment(
            repo=ctx.repo,
            issue_number=ctx.issue_number,
            comment=message,
        )
        logger.info(f"Requested review from {reviewers} for PR #{pr_number}")

    def _build_failure_issue_body(
        self,
        ctx: NotificationContext,
        error_message: str,
    ) -> str:
        """Build the body for a failure notification issue."""
        body = "## AI Automation Failure Report\n\n"
        body += "The automated processing of an issue has failed and requires manual review.\n\n"
        body += "### Details\n\n"
        body += f"- **Original Issue**: #{ctx.issue_number}\n"
        body += f"- **Repository**: {ctx.repo}\n"
        if ctx.branch_name:
            body += f"- **Branch**: `{ctx.branch_name}`\n"
        body += f"\n### Error Message\n\n```\n{error_message}\n```\n\n"
        body += "### Action Required\n\n"
        body += "Please investigate the failure and either:\n"
        body += "1. Fix the issue manually and close this issue\n"
        body += "2. Update the automation configuration and retry\n"
        body += f"3. Close as not planned\n\n"
        body += "---\n"
        body += "_This issue was automatically created by AI Harness._"
        return body

"""
GitHub webhook event handlers.

This module provides handlers for different GitHub webhook event types.
"""

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Supported GitHub webhook event types."""
    ISSUES = "issues"
    ISSUE_COMMENT = "issue_comment"
    PUSH = "push"
    PULL_REQUEST = "pull_request"
    LABEL = "label"


class IssueAction(Enum):
    """GitHub issue event actions."""
    OPENED = "opened"
    EDITED = "edited"
    DELETED = "deleted"
    CLOSED = "closed"
    REOPENED = "reopened"
    LABELED = "labeled"
    UNLABELED = "unlabeled"
    ASSIGNED = "assigned"
    UNASSIGNED = "unassigned"


@dataclass
class IssuePayload:
    """Parsed GitHub issue webhook payload."""
    number: int
    title: str
    body: Optional[str]
    html_url: str
    repository: str
    repository_full_name: str
    sender: str
    labels: list[str] = field(default_factory=list)
    action: str = "opened"
    state: str = "open"

    @classmethod
    def from_webhook(cls, data: Dict[str, Any]) -> "IssuePayload":
        """Create IssuePayload from webhook data."""
        issue = data.get("issue", {})
        repository = data.get("repository", {})
        sender = data.get("sender", {})

        return cls(
            number=issue.get("number", 0),
            title=issue.get("title", ""),
            body=issue.get("body"),
            html_url=issue.get("html_url", ""),
            repository=repository.get("name", ""),
            repository_full_name=repository.get("full_name", ""),
            sender=sender.get("login", ""),
            labels=[label.get("name", "") for label in issue.get("labels", [])],
            action=data.get("action", "opened"),
            state=issue.get("state", "open"),
        )


@dataclass
class WebhookResult:
    """Result of webhook event processing."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class GitHubEventHandler:
    """
    Handles GitHub webhook events.

    This class processes incoming webhook events and dispatches
    them to appropriate handlers based on event type.
    """

    def __init__(
        self,
        on_issue_created: Optional[Callable[[IssuePayload], None]] = None,
        on_issue_closed: Optional[Callable[[IssuePayload], None]] = None,
        on_issue_labeled: Optional[Callable[[IssuePayload], None]] = None,
    ):
        """
        Initialize the event handler.

        Args:
            on_issue_created: Callback for issue created events
            on_issue_closed: Callback for issue closed events
            on_issue_labeled: Callback for issue labeled events
        """
        self._callbacks: Dict[str, Callable] = {
            IssueAction.OPENED.value: on_issue_created,
            IssueAction.CLOSED.value: on_issue_closed,
            IssueAction.LABELED.value: on_issue_labeled,
        }

    def handle_event(
        self,
        event_type: str,
        action: Optional[str],
        payload: Dict[str, Any],
    ) -> WebhookResult:
        """
        Handle a GitHub webhook event.

        Args:
            event_type: The X-GitHub-Event header value
            action: The action field from the payload (if applicable)
            payload: The parsed JSON payload

        Returns:
            WebhookResult indicating success or failure
        """
        logger.info(f"Handling event: {event_type}, action: {action}")

        if event_type == EventType.ISSUES.value:
            return self._handle_issues_event(action, payload)
        elif event_type == EventType.ISSUE_COMMENT.value:
            return self._handle_issue_comment_event(action, payload)
        elif event_type == EventType.PUSH.value:
            return self._handle_push_event(payload)
        elif event_type == EventType.PULL_REQUEST.value:
            return self._handle_pull_request_event(action, payload)
        else:
            logger.warning(f"Unhandled event type: {event_type}")
            return WebhookResult(
                success=True,
                message=f"Event type {event_type} is not handled",
            )

    def _handle_issues_event(
        self,
        action: Optional[str],
        data: Dict[str, Any],
    ) -> WebhookResult:
        """Handle issues event."""
        if not action:
            return WebhookResult(
                success=False,
                message="Missing action in issues event",
                error="No action provided",
            )

        issue_payload = IssuePayload.from_webhook(data)

        # Only process open issues
        if issue_payload.state != "open":
            logger.info(f"Issue #{issue_payload.number} is not open, skipping")
            return WebhookResult(
                success=True,
                message=f"Issue state is {issue_payload.state}, skipping",
                data={"issue_number": issue_payload.number},
            )

        # Dispatch to appropriate callback
        callback = self._callbacks.get(action)
        if callback:
            try:
                callback(issue_payload)
                return WebhookResult(
                    success=True,
                    message=f"Successfully processed issue {action} event",
                    data={
                        "issue_number": issue_payload.number,
                        "repository": issue_payload.repository_full_name,
                    },
                )
            except Exception as e:
                logger.exception(f"Error processing issue event: {e}")
                return WebhookResult(
                    success=False,
                    message=f"Error processing issue event: {e}",
                    error=str(e),
                )
        else:
            logger.info(f"No handler for issue action: {action}")
            return WebhookResult(
                success=True,
                message=f"No handler registered for action: {action}",
            )

    def _handle_issue_comment_event(
        self,
        action: Optional[str],
        data: Dict[str, Any],
    ) -> WebhookResult:
        """Handle issue comment event."""
        # For now, just log the comment
        issue = data.get("issue", {})
        comment = data.get("comment", {})
        logger.info(
            f"Comment on issue #{issue.get('number')}: "
            f"{comment.get('body', '')[:50]}..."
        )
        return WebhookResult(
            success=True,
            message="Issue comment logged",
        )

    def _handle_push_event(self, data: Dict[str, Any]) -> WebhookResult:
        """Handle push event."""
        ref = data.get("ref", "")
        repository = data.get("repository", {}).get("full_name", "")
        commits = data.get("commits", [])
        logger.info(
            f"Push to {repository}:{ref} with {len(commits)} commits"
        )
        return WebhookResult(
            success=True,
            message="Push event logged",
            data={
                "ref": ref,
                "commits_count": len(commits),
            },
        )

    def _handle_pull_request_event(
        self,
        action: Optional[str],
        data: Dict[str, Any],
    ) -> WebhookResult:
        """Handle pull request event."""
        pr = data.get("pull_request", {})
        logger.info(f"Pull request #{pr.get('number')} {action}")
        return WebhookResult(
            success=True,
            message=f"Pull request {action} logged",
            data={"pr_number": pr.get("number")},
        )

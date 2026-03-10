"""
GitHub API client wrapper.

This module provides a simplified interface for common GitHub API
operations needed by the automation pipeline.
"""

import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class PullRequestState(Enum):
    """Pull request states."""
    OPEN = "open"
    CLOSED = "closed"
    ALL = "all"


@dataclass
class Issue:
    """GitHub issue data."""
    number: int
    title: str
    body: Optional[str]
    html_url: str
    state: str
    labels: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Issue":
        """Create Issue from API response dict."""
        return cls(
            number=data.get("number", 0),
            title=data.get("title", ""),
            body=data.get("body"),
            html_url=data.get("html_url", ""),
            state=data.get("state", "open"),
            labels=[l.get("name", "") for l in data.get("labels", [])],
        )


@dataclass
class PullRequest:
    """GitHub pull request data."""
    number: int
    title: str
    body: Optional[str]
    html_url: str
    state: str
    head_ref: str
    base_ref: str
    draft: bool = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PullRequest":
        """Create PullRequest from API response dict."""
        return cls(
            number=data.get("number", 0),
            title=data.get("title", ""),
            body=data.get("body"),
            html_url=data.get("html_url", ""),
            state=data.get("state", "open"),
            head_ref=data.get("head", {}).get("ref", ""),
            base_ref=data.get("base", {}).get("ref", ""),
            draft=data.get("draft", False),
        )


class GitHubClient:
    """
    GitHub API client for automation operations.

    This client wraps PyGithub to provide a simplified interface
    for the automation pipeline.

    Example:
        >>> client = GitHubClient(token="ghp_xxx")
        >>> issue = client.create_issue(
        ...     repo="owner/repo",
        ...     title="Bug found",
        ...     body="Description here"
        ... )
    """

    def __init__(
        self,
        token: Optional[str] = None,
        api_base: str = "https://api.github.com",
    ):
        """
        Initialize the GitHub client.

        Args:
            token: GitHub personal access token (or from GITHUB_TOKEN env)
            api_base: GitHub API base URL
        """
        self.token = token or os.environ.get("GITHUB_TOKEN")
        self.api_base = api_base
        self._github = None

        if not self.token:
            logger.warning("No GitHub token provided")

    def _get_github(self):
        """Get or create PyGithub instance."""
        if self._github is None:
            try:
                from github import Github
                self._github = Github(self.token, base_url=self.api_base)
            except ImportError:
                raise ImportError(
                    "PyGithub is required. Install with: pip install PyGithub"
                )
        return self._github

    def _parse_repo_name(self, repo: str) -> tuple:
        """Parse 'owner/repo' format to (owner, repo)."""
        parts = repo.split("/")
        if len(parts) != 2:
            raise ValueError(f"Invalid repo format: {repo}, expected 'owner/repo'")
        return parts[0], parts[1]

    def get_repo(self, repo: str):
        """Get a repository object."""
        github = self._get_github()
        return github.get_repo(repo)

    def get_issue(self, repo: str, issue_number: int) -> Issue:
        """
        Get an issue by number.

        Args:
            repo: Repository in 'owner/repo' format
            issue_number: Issue number

        Returns:
            Issue object
        """
        repository = self.get_repo(repo)
        issue = repository.get_issue(issue_number)
        return Issue.from_dict(issue.raw_data)

    def create_issue(
        self,
        repo: str,
        title: str,
        body: Optional[str] = None,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
    ) -> Issue:
        """
        Create a new issue.

        Args:
            repo: Repository in 'owner/repo' format
            title: Issue title
            body: Issue body/description
            labels: List of label names to apply
            assignees: List of usernames to assign

        Returns:
            Created Issue object
        """
        repository = self.get_repo(repo)
        issue = repository.create_issue(
            title=title,
            body=body or "",
            labels=labels or [],
            assignees=assignees or [],
        )
        logger.info(f"Created issue #{issue.number} in {repo}")
        return Issue.from_dict(issue.raw_data)

    def add_issue_comment(
        self,
        repo: str,
        issue_number: int,
        comment: str,
    ) -> None:
        """
        Add a comment to an issue.

        Args:
            repo: Repository in 'owner/repo' format
            issue_number: Issue number
            comment: Comment body
        """
        repository = self.get_repo(repo)
        issue = repository.get_issue(issue_number)
        issue.create_comment(comment)
        logger.info(f"Added comment to issue #{issue_number} in {repo}")

    def close_issue(self, repo: str, issue_number: int) -> None:
        """
        Close an issue.

        Args:
            repo: Repository in 'owner/repo' format
            issue_number: Issue number
        """
        repository = self.get_repo(repo)
        issue = repository.get_issue(issue_number)
        issue.edit(state="closed")
        logger.info(f"Closed issue #{issue_number} in {repo}")

    def create_pull_request(
        self,
        repo: str,
        title: str,
        head: str,
        base: str = "main",
        body: Optional[str] = None,
        draft: bool = False,
    ) -> PullRequest:
        """
        Create a pull request.

        Args:
            repo: Repository in 'owner/repo' format
            title: PR title
            head: Source branch name
            base: Target branch name
            body: PR description
            draft: Whether to create as draft PR

        Returns:
            Created PullRequest object
        """
        repository = self.get_repo(repo)
        pr = repository.create_pull(
            title=title,
            body=body or "",
            head=head,
            base=base,
            draft=draft,
        )
        logger.info(f"Created PR #{pr.number} in {repo}: {head} -> {base}")
        return PullRequest.from_dict(pr.raw_data)

    def get_pull_requests(
        self,
        repo: str,
        state: PullRequestState = PullRequestState.OPEN,
        head: Optional[str] = None,
        base: Optional[str] = None,
    ) -> List[PullRequest]:
        """
        List pull requests.

        Args:
            repo: Repository in 'owner/repo' format
            state: PR state filter
            head: Filter by head branch
            base: Filter by base branch

        Returns:
            List of PullRequest objects
        """
        repository = self.get_repo(repo)
        prs = repository.get_pulls(
            state=state.value,
            head=head,
            base=base,
        )
        return [PullRequest.from_dict(pr.raw_data) for pr in prs]

    def request_review(
        self,
        repo: str,
        pr_number: int,
        reviewers: List[str],
    ) -> None:
        """
        Request reviewers for a pull request.

        Args:
            repo: Repository in 'owner/repo' format
            pr_number: PR number
            reviewers: List of reviewer usernames
        """
        repository = self.get_repo(repo)
        pr = repository.get_pull(pr_number)
        pr.create_review_request(reviewers=reviewers)
        logger.info(f"Requested review from {reviewers} on PR #{pr_number}")

    def add_pr_comment(
        self,
        repo: str,
        pr_number: int,
        comment: str,
    ) -> None:
        """
        Add a comment to a pull request.

        Args:
            repo: Repository in 'owner/repo' format
            pr_number: PR number
            comment: Comment body
        """
        repository = self.get_repo(repo)
        pr = repository.get_pull(pr_number)
        pr.create_issue_comment(comment)
        logger.info(f"Added comment to PR #{pr_number} in {repo}")

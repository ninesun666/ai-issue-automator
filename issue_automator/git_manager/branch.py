"""
Branch management for automation pipeline.

This module provides functionality for creating and managing
Git branches based on issue types.
"""

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

logger = logging.getLogger(__name__)


class BranchType(Enum):
    """Types of branches based on issue type."""
    FEATURE = "feat"
    BUGFIX = "fix"
    HOTFIX = "hotfix"
    DOCUMENTATION = "docs"
    REFACTOR = "refactor"
    TEST = "test"
    UNKNOWN = "misc"


@dataclass
class BranchInfo:
    """Information about a branch."""
    name: str
    branch_type: BranchType
    issue_number: Optional[int]
    description: str

    @classmethod
    def parse(cls, branch_name: str) -> "BranchInfo":
        """Parse branch name to extract information."""
        # Common patterns:
        # feat/issue-123-add-login
        # fix/issue-456-memory-leak
        # feature/123-add-login
        # bugfix/456-fix-crash
        
        patterns = [
            # feat/issue-123-description
            r"^(feat|feature|fix|bugfix|hotfix|docs|refactor|test|misc)/issue-(\d+)-(.+)$",
            # feat/123-description
            r"^(feat|feature|fix|bugfix|hotfix|docs|refactor|test|misc)/(\d+)-(.+)$",
            # feat/description (no issue number)
            r"^(feat|feature|fix|bugfix|hotfix|docs|refactor|test|misc)/(.+)$",
        ]

        for pattern in patterns:
            match = re.match(pattern, branch_name)
            if match:
                groups = match.groups()
                branch_type = cls._map_branch_type(groups[0])
                
                if len(groups) == 3:
                    # Has issue number
                    issue_num = int(groups[1]) if groups[1].isdigit() else None
                    description = groups[2]
                else:
                    # No issue number
                    issue_num = None
                    description = groups[1]
                
                return cls(
                    name=branch_name,
                    branch_type=branch_type,
                    issue_number=issue_num,
                    description=description.replace("-", " "),
                )

        # Unknown format
        return cls(
            name=branch_name,
            branch_type=BranchType.UNKNOWN,
            issue_number=None,
            description=branch_name,
        )

    @staticmethod
    def _map_branch_type(prefix: str) -> BranchType:
        """Map branch prefix to BranchType."""
        mapping = {
            "feat": BranchType.FEATURE,
            "feature": BranchType.FEATURE,
            "fix": BranchType.BUGFIX,
            "bugfix": BranchType.BUGFIX,
            "hotfix": BranchType.HOTFIX,
            "docs": BranchType.DOCUMENTATION,
            "refactor": BranchType.REFACTOR,
            "test": BranchType.TEST,
            "misc": BranchType.UNKNOWN,
        }
        return mapping.get(prefix.lower(), BranchType.UNKNOWN)


class BranchManager:
    """
    Manages Git branch operations.

    This class handles creating, switching, and managing branches
    for the automation pipeline.

    Example:
        >>> manager = BranchManager(repo_manager)
        >>> branch = manager.create_branch_for_issue(
        ...     "owner/repo",
        ...     issue_number=123,
        ...     issue_type="feature",
        ...     title="Add login feature"
        ... )
    """

    # Mapping from issue labels to branch types
    LABEL_TO_BRANCH_TYPE = {
        "feature": BranchType.FEATURE,
        "enhancement": BranchType.FEATURE,
        "bug": BranchType.BUGFIX,
        "fix": BranchType.BUGFIX,
        "hotfix": BranchType.HOTFIX,
        "documentation": BranchType.DOCUMENTATION,
        "docs": BranchType.DOCUMENTATION,
        "refactor": BranchType.REFACTOR,
        "test": BranchType.TEST,
    }

    def __init__(self, repository_manager):
        """
        Initialize the branch manager.

        Args:
            repository_manager: RepositoryManager instance
        """
        self.repo_manager = repository_manager

    def create_branch_for_issue(
        self,
        full_name: str,
        issue_number: int,
        issue_title: str,
        issue_labels: Optional[List[str]] = None,
        base_branch: str = "main",
    ) -> str:
        """
        Create a new branch for an issue.

        Args:
            full_name: Repository name in 'owner/repo' format
            issue_number: GitHub issue number
            issue_title: Issue title (used for branch name)
            issue_labels: Issue labels (used to determine branch type)
            base_branch: Base branch to create from

        Returns:
            Name of the created branch
        """
        # Determine branch type from labels
        branch_type = self._determine_branch_type(issue_labels)

        # Generate branch name
        branch_name = self._generate_branch_name(
            branch_type=branch_type,
            issue_number=issue_number,
            title=issue_title,
        )

        # Create the branch
        self._create_branch(full_name, branch_name, base_branch)

        return branch_name

    def _determine_branch_type(
        self,
        labels: Optional[List[str]],
    ) -> BranchType:
        """Determine branch type from issue labels."""
        if not labels:
            return BranchType.FEATURE  # Default

        for label in labels:
            label_lower = label.lower()
            if label_lower in self.LABEL_TO_BRANCH_TYPE:
                return self.LABEL_TO_BRANCH_TYPE[label_lower]

        return BranchType.FEATURE  # Default

    def _generate_branch_name(
        self,
        branch_type: BranchType,
        issue_number: int,
        title: str,
    ) -> str:
        """Generate a branch name from components."""
        # Sanitize title for branch name
        sanitized_title = self._sanitize_title(title)
        
        # Format: {type}/issue-{number}-{title}
        branch_name = f"{branch_type.value}/issue-{issue_number}-{sanitized_title}"
        
        # Limit length
        if len(branch_name) > 100:
            branch_name = branch_name[:100].rstrip("-")
        
        return branch_name

    def _sanitize_title(self, title: str) -> str:
        """Sanitize title for use in branch name."""
        # Remove special characters
        sanitized = re.sub(r"[^a-zA-Z0-9\s-]", "", title)
        # Replace spaces with hyphens
        sanitized = re.sub(r"\s+", "-", sanitized)
        # Remove consecutive hyphens
        sanitized = re.sub(r"-+", "-", sanitized)
        # Convert to lowercase
        sanitized = sanitized.lower()
        # Remove leading/trailing hyphens
        sanitized = sanitized.strip("-")
        
        return sanitized

    def _create_branch(
        self,
        full_name: str,
        branch_name: str,
        base_branch: str,
    ) -> None:
        """Create a new branch in the repository."""
        repo = self.repo_manager.get_local_repo(full_name)
        
        # Fetch latest
        repo.remotes.origin.fetch()
        
        # Check if branch exists
        if branch_name in [h.name for h in repo.heads]:
            logger.info(f"Branch {branch_name} already exists, checking out")
            repo.git.checkout(branch_name)
            return

        # Ensure we're on base branch
        try:
            repo.git.checkout(base_branch)
        except Exception:
            # Try 'master' if 'main' doesn't exist
            repo.git.checkout("master")
        
        # Pull latest changes
        repo.remotes.origin.pull()
        
        # Create and checkout new branch
        repo.git.checkout("-b", branch_name)
        logger.info(f"Created and checked out branch: {branch_name}")

    def switch_branch(self, full_name: str, branch_name: str) -> None:
        """Switch to an existing branch."""
        repo = self.repo_manager.get_local_repo(full_name)
        repo.git.checkout(branch_name)
        logger.info(f"Switched to branch: {branch_name}")

    def delete_branch(
        self,
        full_name: str,
        branch_name: str,
        force: bool = False,
    ) -> None:
        """Delete a branch."""
        repo = self.repo_manager.get_local_repo(full_name)
        
        # Switch to main/master first
        try:
            repo.git.checkout("main")
        except Exception:
            repo.git.checkout("master")
        
        # Delete the branch
        if force:
            repo.git.branch("-D", branch_name)
        else:
            repo.git.branch("-d", branch_name)
        
        logger.info(f"Deleted branch: {branch_name}")

    def list_branches(self, full_name: str) -> List[BranchInfo]:
        """List all branches in the repository."""
        repo = self.repo_manager.get_local_repo(full_name)
        
        branches = []
        for head in repo.heads:
            branches.append(BranchInfo.parse(head.name))
        
        return branches

    def get_current_branch(self, full_name: str) -> BranchInfo:
        """Get the current branch."""
        branch_name = self.repo_manager.get_current_branch(full_name)
        return BranchInfo.parse(branch_name)

    def branch_exists(self, full_name: str, branch_name: str) -> bool:
        """Check if a branch exists."""
        repo = self.repo_manager.get_local_repo(full_name)
        return branch_name in [h.name for h in repo.heads]

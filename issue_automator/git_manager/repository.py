"""
Repository management for automation pipeline.

This module provides functionality for cloning, fetching, and
managing local copies of Git repositories.
"""

import logging
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class RepositoryInfo:
    """Information about a repository."""
    owner: str
    name: str
    full_name: str  # owner/name
    clone_url: str
    local_path: Path

    @classmethod
    def from_full_name(
        cls,
        full_name: str,
        local_path: Path,
        use_ssh: bool = False,
    ) -> "RepositoryInfo":
        """Create RepositoryInfo from 'owner/name' format."""
        parts = full_name.split("/")
        if len(parts) != 2:
            raise ValueError(f"Invalid repository name: {full_name}")
        
        owner, name = parts
        if use_ssh:
            clone_url = f"git@github.com:{owner}/{name}.git"
        else:
            clone_url = f"https://github.com/{owner}/{name}.git"
        
        return cls(
            owner=owner,
            name=name,
            full_name=full_name,
            clone_url=clone_url,
            local_path=local_path,
        )


class RepositoryManager:
    """
    Manages Git repository operations.

    This class handles cloning, fetching, and managing local
    copies of repositories for the automation pipeline.

    Example:
        >>> manager = RepositoryManager(work_dir=Path("./repos"))
        >>> repo = manager.clone_or_fetch("owner/repo")
        >>> print(repo.local_path)
    """

    def __init__(
        self,
        work_dir: Path,
        use_ssh: bool = False,
        github_token: Optional[str] = None,
    ):
        """
        Initialize the repository manager.

        Args:
            work_dir: Base directory for cloning repositories
            use_ssh: Use SSH for cloning instead of HTTPS
            github_token: GitHub token for authenticated HTTPS cloning
        """
        self.work_dir = Path(work_dir)
        self.use_ssh = use_ssh
        self.github_token = github_token
        self._repos: dict[str, RepositoryInfo] = {}

        # Ensure work directory exists
        self.work_dir.mkdir(parents=True, exist_ok=True)

    def _get_git(self):
        """Get GitPython Repo class lazily."""
        try:
            from git import Repo
            return Repo
        except ImportError:
            raise ImportError(
                "GitPython is required. Install with: pip install GitPython"
            )

    def get_repo_path(self, full_name: str) -> Path:
        """Get the local path for a repository."""
        return self.work_dir / full_name.replace("/", os.sep)

    def clone_or_fetch(
        self,
        full_name: str,
        branch: Optional[str] = None,
    ) -> RepositoryInfo:
        """
        Clone a repository or fetch latest if it exists.

        Args:
            full_name: Repository name in 'owner/repo' format
            branch: Optional branch to checkout

        Returns:
            RepositoryInfo for the repository
        """
        Repo = self._get_git()
        local_path = self.get_repo_path(full_name)
        
        repo_info = RepositoryInfo.from_full_name(
            full_name,
            local_path,
            use_ssh=self.use_ssh,
        )

        if local_path.exists():
            # Repository exists, fetch latest
            logger.info(f"Fetching existing repository: {full_name}")
            repo = Repo(local_path)
            
            # Fetch all remotes
            for remote in repo.remotes:
                remote.fetch()
            
            # Checkout requested branch
            if branch:
                self._checkout_branch(repo, branch)
        else:
            # Clone the repository
            logger.info(f"Cloning repository: {full_name}")
            clone_url = self._get_authenticated_url(repo_info.clone_url)
            
            if branch:
                repo = Repo.clone_from(
                    clone_url,
                    local_path,
                    branch=branch,
                )
            else:
                repo = Repo.clone_from(clone_url, local_path)

        self._repos[full_name] = repo_info
        return repo_info

    def _get_authenticated_url(self, url: str) -> str:
        """Add authentication to URL if token is provided."""
        if self.github_token and url.startswith("https://"):
            # Insert token into URL
            return url.replace(
                "https://",
                f"https://{self.github_token}@",
            )
        return url

    def _checkout_branch(self, repo, branch: str) -> None:
        """Checkout a branch in the repository."""
        try:
            # Try to checkout local branch
            repo.git.checkout(branch)
        except Exception:
            # Try to checkout remote branch
            try:
                repo.git.checkout("-b", branch, f"origin/{branch}")
            except Exception as e:
                logger.warning(f"Failed to checkout branch {branch}: {e}")

    def get_local_repo(self, full_name: str):
        """Get a GitPython Repo object for a cloned repository."""
        Repo = self._get_git()
        local_path = self.get_repo_path(full_name)
        
        if not local_path.exists():
            raise ValueError(f"Repository not cloned: {full_name}")
        
        return Repo(local_path)

    def clean_repo(self, full_name: str) -> None:
        """Remove a cloned repository from local storage."""
        local_path = self.get_repo_path(full_name)
        
        if local_path.exists():
            shutil.rmtree(local_path)
            logger.info(f"Removed repository: {full_name}")
        
        if full_name in self._repos:
            del self._repos[full_name]

    def list_cloned_repos(self) -> list[str]:
        """List all cloned repository names."""
        repos = []
        for owner_dir in self.work_dir.iterdir():
            if owner_dir.is_dir():
                for repo_dir in owner_dir.iterdir():
                    if repo_dir.is_dir() and (repo_dir / ".git").exists():
                        repos.append(f"{owner_dir.name}/{repo_dir.name}")
        return repos

    def get_current_branch(self, full_name: str) -> str:
        """Get the current branch name of a repository."""
        repo = self.get_local_repo(full_name)
        return repo.active_branch.name

    def has_uncommitted_changes(self, full_name: str) -> bool:
        """Check if repository has uncommitted changes."""
        repo = self.get_local_repo(full_name)
        return repo.is_dirty()

    def get_status(self, full_name: str) -> dict:
        """Get repository status information."""
        repo = self.get_local_repo(full_name)
        
        return {
            "current_branch": repo.active_branch.name,
            "is_dirty": repo.is_dirty(),
            "untracked_files": repo.untracked_files,
            "head_commit": repo.head.commit.hexsha[:8],
        }

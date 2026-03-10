"""
Git manager module for repository operations.

This module provides functionality for managing Git repositories,
branches, and pull requests in the automation pipeline.
"""

from issue_automator.git_manager.repository import RepositoryManager
from issue_automator.git_manager.branch import BranchManager, BranchType
from issue_automator.git_manager.pull_request import PRManager

__all__ = [
    "RepositoryManager",
    "BranchManager",
    "BranchType",
    "PRManager",
]

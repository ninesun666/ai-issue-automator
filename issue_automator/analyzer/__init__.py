"""
Analyzer module for GitHub issue analysis.

This module provides functionality to parse and analyze GitHub issues,
and to split requirements into actionable tasks using iFlow CLI.
"""

from issue_automator.analyzer.issue_parser import IssueParser, ParsedIssue
from issue_automator.analyzer.requirement_splitter import RequirementSplitter
from issue_automator.analyzer.prompts import (
    ISSUE_ANALYSIS_PROMPT,
    REQUIREMENT_SPLIT_PROMPT,
    TASK_GENERATION_PROMPT,
)

__all__ = [
    "IssueParser",
    "ParsedIssue",
    "RequirementSplitter",
    "ISSUE_ANALYSIS_PROMPT",
    "REQUIREMENT_SPLIT_PROMPT",
    "TASK_GENERATION_PROMPT",
]

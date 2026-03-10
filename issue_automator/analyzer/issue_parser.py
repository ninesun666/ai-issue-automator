"""
GitHub issue parser.

This module provides functionality to parse and extract structured
information from GitHub issues.
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class IssueType(Enum):
    """Types of issues."""
    FEATURE = "feature"
    BUG = "bug"
    ENHANCEMENT = "enhancement"
    DOCUMENTATION = "documentation"
    UNKNOWN = "unknown"


class Priority(Enum):
    """Issue priority levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


@dataclass
class ParsedIssue:
    """Parsed issue data with extracted metadata."""
    number: int
    title: str
    body: Optional[str]
    html_url: str
    repository: str
    repository_full_name: str
    sender: str
    labels: List[str] = field(default_factory=list)
    
    # Parsed fields
    issue_type: IssueType = IssueType.UNKNOWN
    priority: Priority = Priority.MEDIUM
    summary: str = ""
    description: str = ""
    acceptance_criteria: List[str] = field(default_factory=list)
    technical_notes: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "number": self.number,
            "title": self.title,
            "body": self.body,
            "html_url": self.html_url,
            "repository": self.repository,
            "repository_full_name": self.repository_full_name,
            "sender": self.sender,
            "labels": self.labels,
            "issue_type": self.issue_type.value,
            "priority": self.priority.value,
            "summary": self.summary,
            "description": self.description,
            "acceptance_criteria": self.acceptance_criteria,
            "technical_notes": self.technical_notes,
            "dependencies": self.dependencies,
        }


class IssueParser:
    """
    Parser for GitHub issues.

    This class extracts structured information from GitHub issue
    content, including type, priority, and requirements.

    Example:
        >>> parser = IssueParser()
        >>> parsed = parser.parse(issue_payload)
        >>> print(parsed.issue_type)
        <IssueType.FEATURE: 'feature'>
    """

    # Label patterns for issue type detection
    FEATURE_LABELS = {"feature", "enhancement", "new-feature"}
    BUG_LABELS = {"bug", "fix", "defect"}
    DOCS_LABELS = {"documentation", "docs"}
    
    # Priority label patterns
    PRIORITY_LABELS = {
        Priority.CRITICAL: {"critical", "urgent", "p0"},
        Priority.HIGH: {"high", "important", "p1"},
        Priority.MEDIUM: {"medium", "normal", "p2"},
        Priority.LOW: {"low", "minor", "p3"},
    }

    # Markdown patterns
    HEADING_PATTERN = re.compile(r"^#+\s+(.+)$", re.MULTILINE)
    CHECKLIST_PATTERN = re.compile(r"-\s*\[([ x])\]\s*(.+)$", re.MULTILINE)
    LIST_PATTERN = re.compile(r"^\s*[-*]\s+(.+)$", re.MULTILINE)

    def parse(self, issue_data: dict) -> ParsedIssue:
        """
        Parse an issue from webhook payload data.

        Args:
            issue_data: Raw issue data from GitHub webhook

        Returns:
            ParsedIssue with extracted metadata
        """
        issue = issue_data.get("issue", {})
        repository = issue_data.get("repository", {})
        sender = issue_data.get("sender", {})

        parsed = ParsedIssue(
            number=issue.get("number", 0),
            title=issue.get("title", ""),
            body=issue.get("body"),
            html_url=issue.get("html_url", ""),
            repository=repository.get("name", ""),
            repository_full_name=repository.get("full_name", ""),
            sender=sender.get("login", ""),
            labels=[label.get("name", "") for label in issue.get("labels", [])],
        )

        # Extract type and priority from labels
        parsed.issue_type = self._detect_issue_type(parsed.labels)
        parsed.priority = self._detect_priority(parsed.labels)

        # Parse body content
        if parsed.body:
            self._parse_body(parsed)

        # Generate summary if not extracted
        if not parsed.summary:
            parsed.summary = parsed.title

        return parsed

    def _detect_issue_type(self, labels: List[str]) -> IssueType:
        """Detect issue type from labels."""
        label_set = {l.lower() for l in labels}
        
        if label_set & self.FEATURE_LABELS:
            return IssueType.FEATURE
        if label_set & self.BUG_LABELS:
            return IssueType.BUG
        if label_set & self.DOCS_LABELS:
            return IssueType.DOCUMENTATION
        
        return IssueType.UNKNOWN

    def _detect_priority(self, labels: List[str]) -> Priority:
        """Detect priority from labels."""
        label_set = {l.lower() for l in labels}
        
        for priority, patterns in self.PRIORITY_LABELS.items():
            if label_set & patterns:
                return priority
        
        return Priority.MEDIUM

    def _parse_body(self, parsed: ParsedIssue) -> None:
        """Parse issue body for structured content."""
        body = parsed.body

        # Look for acceptance criteria sections
        criteria_section = self._extract_section(
            body,
            ["acceptance criteria", "criteria", "requirements", "验收标准"]
        )
        if criteria_section:
            parsed.acceptance_criteria = self._extract_list_items(criteria_section)

        # Look for technical notes sections
        tech_section = self._extract_section(
            body,
            ["technical notes", "implementation notes", "技术说明", "实现说明"]
        )
        if tech_section:
            parsed.technical_notes = self._extract_list_items(tech_section)

        # Look for dependencies sections
        deps_section = self._extract_section(
            body,
            ["dependencies", "depends on", "依赖"]
        )
        if deps_section:
            parsed.dependencies = self._extract_list_items(deps_section)

        # Extract description (first paragraph or content before sections)
        parsed.description = self._extract_description(body)

    def _extract_section(self, body: str, heading_keywords: List[str]) -> Optional[str]:
        """Extract content under a heading matching keywords."""
        lines = body.split("\n")
        in_section = False
        section_lines = []

        for line in lines:
            # Check if this is a heading
            heading_match = self.HEADING_PATTERN.match(line.strip())
            if heading_match:
                heading_text = heading_match.group(1).lower()
                if any(kw in heading_text for kw in heading_keywords):
                    in_section = True
                    continue
                elif in_section:
                    # Found another heading, stop
                    break
            
            if in_section:
                section_lines.append(line)

        return "\n".join(section_lines).strip() if section_lines else None

    def _extract_list_items(self, text: str) -> List[str]:
        """Extract list items from text."""
        items = []
        for match in self.LIST_PATTERN.finditer(text):
            items.append(match.group(1).strip())
        for match in self.CHECKLIST_PATTERN.finditer(text):
            items.append(match.group(2).strip())
        return items

    def _extract_description(self, body: str) -> str:
        """Extract the main description from issue body."""
        # Split by headings and take the first part
        parts = self.HEADING_PATTERN.split(body)
        if parts:
            description = parts[0].strip()
            # Take first paragraph
            paragraphs = description.split("\n\n")
            if paragraphs:
                return paragraphs[0].strip()
        return ""

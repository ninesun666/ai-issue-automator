"""
Requirement splitter using iFlow CLI.

This module uses iFlow CLI to analyze issues and split them
into actionable tasks with detailed implementation steps.
"""

import json
import logging
import os
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from issue_automator.analyzer.issue_parser import ParsedIssue
from issue_automator.analyzer.prompts import (
    ISSUE_ANALYSIS_PROMPT,
    REQUIREMENT_SPLIT_PROMPT,
)

logger = logging.getLogger(__name__)


@dataclass
class Task:
    """A single task derived from an issue."""
    id: str
    title: str
    description: str
    priority: str = "medium"
    dependencies: List[str] = field(default_factory=list)
    files_to_modify: List[str] = field(default_factory=list)
    estimated_complexity: str = "medium"
    passes: bool = False

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "dependencies": self.dependencies,
            "files_to_modify": self.files_to_modify,
            "estimated_complexity": self.estimated_complexity,
            "passes": self.passes,
        }


@dataclass
class AnalysisResult:
    """Result of issue analysis."""
    issue_number: int
    summary: str
    tasks: List[Task] = field(default_factory=list)
    overall_approach: str = ""
    potential_risks: List[str] = field(default_factory=list)
    raw_response: str = ""

    def to_feature_list(self) -> Dict[str, Any]:
        """Convert to feature_list.json format."""
        return {
            "project": {
                "source_issue": self.issue_number,
            },
            "features": [
                {
                    "id": task.id,
                    "description": task.title,
                    "details": task.description,
                    "priority": task.priority,
                    "dependencies": task.dependencies,
                    "files_to_modify": task.files_to_modify,
                    "estimated_complexity": task.estimated_complexity,
                    "passes": task.passes,
                }
                for task in self.tasks
            ],
            "overall_approach": self.overall_approach,
            "potential_risks": self.potential_risks,
        }


class RequirementSplitter:
    """
    Analyzes issues and splits requirements into tasks using iFlow CLI.

    This class uses iFlow CLI to perform intelligent analysis of
    GitHub issues and generate structured task lists.

    Example:
        >>> splitter = RequirementSplitter()
        >>> result = splitter.analyze(parsed_issue)
        >>> feature_list = result.to_feature_list()
    """

    def __init__(
        self,
        iflow_path: Optional[str] = None,
        max_turns: int = 30,
        timeout: int = 600,
    ):
        """
        Initialize the requirement splitter.

        Args:
            iflow_path: Path to iFlow CLI executable
            max_turns: Maximum turns for iFlow execution
            timeout: Timeout in seconds for iFlow execution
        """
        self.iflow_path = iflow_path or self._find_iflow()
        self.max_turns = max_turns
        self.timeout = timeout

    def _find_iflow(self) -> str:
        """Find iFlow CLI in common locations."""
        # Check common locations
        common_paths = [
            "iflow",
            "iflow.exe",
            os.path.expanduser("~/.local/bin/iflow"),
            os.path.expanduser("~/AppData/Local/Programs/iflow/iflow.exe"),
        ]
        
        for path in common_paths:
            if os.path.isfile(path) or self._is_in_path(path):
                return path
        
        # Default to 'iflow' assuming it's in PATH
        return "iflow"

    def _is_in_path(self, command: str) -> bool:
        """Check if command is in PATH."""
        try:
            result = subprocess.run(
                ["where", command] if os.name == "nt" else ["which", command],
                capture_output=True,
                text=True,
            )
            return result.returncode == 0
        except Exception:
            return False

    def analyze(
        self,
        issue: ParsedIssue,
        repo_context: Optional[str] = None,
    ) -> AnalysisResult:
        """
        Analyze an issue and generate task breakdown.

        Args:
            issue: Parsed issue to analyze
            repo_context: Optional repository context/description

        Returns:
            AnalysisResult with task breakdown
        """
        logger.info(f"Analyzing issue #{issue.number}: {issue.title}")

        # Build the analysis prompt
        prompt = self._build_prompt(issue, repo_context)

        # Execute iFlow CLI
        response = self._execute_iflow(prompt)

        # Parse the response
        result = self._parse_response(issue.number, response)

        return result

    def _build_prompt(
        self,
        issue: ParsedIssue,
        repo_context: Optional[str] = None,
    ) -> str:
        """Build the analysis prompt for iFlow."""
        prompt = ISSUE_ANALYSIS_PROMPT.format(
            issue_number=issue.number,
            issue_title=issue.title,
            issue_body=issue.body or "No description provided",
            issue_type=issue.issue_type.value,
            issue_priority=issue.priority.value,
            labels=", ".join(issue.labels),
            acceptance_criteria="\n".join(f"- {c}" for c in issue.acceptance_criteria)
            if issue.acceptance_criteria
            else "Not specified",
            repo_context=repo_context or "Not specified",
        )
        return prompt

    def _execute_iflow(self, prompt: str) -> str:
        """Execute iFlow CLI with the given prompt."""
        logger.info("Executing iFlow CLI for analysis...")

        try:
            # Create a temporary file for the prompt
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".txt",
                delete=False,
                encoding="utf-8",
            ) as f:
                f.write(prompt)
                prompt_file = f.name

            try:
                cmd = [
                    self.iflow_path,
                    "-p", prompt_file,
                    "--yolo",
                    f"--max-turns={self.max_turns}",
                ]

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                    encoding="utf-8",
                )

                if result.returncode != 0:
                    logger.error(f"iFlow failed: {result.stderr}")
                    raise RuntimeError(f"iFlow execution failed: {result.stderr}")

                return result.stdout

            finally:
                # Clean up temp file
                os.unlink(prompt_file)

        except subprocess.TimeoutExpired:
            logger.error("iFlow execution timed out")
            raise RuntimeError("iFlow execution timed out")
        except Exception as e:
            logger.error(f"Error executing iFlow: {e}")
            raise

    def _parse_response(
        self,
        issue_number: int,
        response: str,
    ) -> AnalysisResult:
        """Parse iFlow response into structured result."""
        result = AnalysisResult(
            issue_number=issue_number,
            summary="",
            raw_response=response,
        )

        # Try to extract JSON from response
        json_match = self._extract_json(response)
        if json_match:
            try:
                data = json.loads(json_match)
                result.summary = data.get("summary", "")
                result.overall_approach = data.get("overall_approach", "")
                result.potential_risks = data.get("potential_risks", [])

                for i, task_data in enumerate(data.get("tasks", [])):
                    task = Task(
                        id=task_data.get("id", f"T{i+1:03d}"),
                        title=task_data.get("title", ""),
                        description=task_data.get("description", ""),
                        priority=task_data.get("priority", "medium"),
                        dependencies=task_data.get("dependencies", []),
                        files_to_modify=task_data.get("files_to_modify", []),
                        estimated_complexity=task_data.get("estimated_complexity", "medium"),
                        passes=False,
                    )
                    result.tasks.append(task)

            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON from response: {e}")
                # Fall back to basic parsing
                result = self._fallback_parse(issue_number, response)
        else:
            # No JSON found, use fallback parsing
            result = self._fallback_parse(issue_number, response)

        return result

    def _extract_json(self, text: str) -> Optional[str]:
        """Extract JSON block from text."""
        # Look for JSON code blocks
        import re
        
        # Try ```json ... ``` blocks
        json_block = re.search(r"```json\s*\n(.*?)\n```", text, re.DOTALL)
        if json_block:
            return json_block.group(1)

        # Try { ... } patterns
        brace_start = text.find("{")
        if brace_start != -1:
            brace_count = 0
            for i, char in enumerate(text[brace_start:], brace_start):
                if char == "{":
                    brace_count += 1
                elif char == "}":
                    brace_count -= 1
                    if brace_count == 0:
                        return text[brace_start:i+1]

        return None

    def _fallback_parse(
        self,
        issue_number: int,
        response: str,
    ) -> AnalysisResult:
        """Fallback parsing when JSON extraction fails."""
        result = AnalysisResult(
            issue_number=issue_number,
            summary=f"Automated analysis of issue #{issue_number}",
            raw_response=response,
        )

        # Create a single task from the issue
        result.tasks.append(Task(
            id="T001",
            title=f"Implement solution for issue #{issue_number}",
            description=response[:1000] if response else "No details available",
            priority="medium",
            passes=False,
        ))

        return result

    def generate_feature_list_file(
        self,
        result: AnalysisResult,
        output_path: Path,
    ) -> Path:
        """
        Generate a feature_list.json file from analysis result.

        Args:
            result: Analysis result
            output_path: Directory to create the file in

        Returns:
            Path to the created file
        """
        harness_dir = output_path / ".agent-harness"
        harness_dir.mkdir(parents=True, exist_ok=True)

        feature_list_path = harness_dir / "feature_list.json"
        
        with open(feature_list_path, "w", encoding="utf-8") as f:
            json.dump(result.to_feature_list(), f, indent=2, ensure_ascii=False)

        logger.info(f"Generated feature list at {feature_list_path}")
        return feature_list_path

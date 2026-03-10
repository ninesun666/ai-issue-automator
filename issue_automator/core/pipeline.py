"""
Automation pipeline for issue processing.

This module orchestrates the complete workflow from issue receipt
to PR creation, including analysis, task breakdown, execution,
and notification.
"""

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from issue_automator.analyzer.issue_parser import IssueParser, ParsedIssue
from issue_automator.analyzer.requirement_splitter import RequirementSplitter, AnalysisResult
from issue_automator.git_manager.repository import RepositoryManager
from issue_automator.git_manager.branch import BranchManager, BranchType
from issue_automator.git_manager.pull_request import PRManager
from issue_automator.notification.github_client import GitHubClient
from issue_automator.notification.notifier import Notifier, NotificationContext

logger = logging.getLogger(__name__)


class PipelineState(Enum):
    """States of the automation pipeline."""
    IDLE = "idle"
    ANALYZING = "analyzing"
    PREPARING_REPO = "preparing_repo"
    CREATING_BRANCH = "creating_branch"
    EXECUTING = "executing"
    PUSHING = "pushing"
    CREATING_PR = "creating_pr"
    NOTIFYING = "notifying"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class PipelineResult:
    """Result of pipeline execution."""
    success: bool
    state: PipelineState
    message: str
    issue_number: int
    repo: str
    branch: Optional[str] = None
    pr_number: Optional[int] = None
    pr_url: Optional[str] = None
    error: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "state": self.state.value,
            "message": self.message,
            "issue_number": self.issue_number,
            "repo": self.repo,
            "branch": self.branch,
            "pr_number": self.pr_number,
            "pr_url": self.pr_url,
            "error": self.error,
            "data": self.data,
        }


class AutomationPipeline:
    """
    Main automation pipeline for processing GitHub issues.

    This class orchestrates the complete workflow:
    1. Parse and analyze the issue
    2. Prepare the repository (clone/fetch)
    3. Create a feature branch
    4. Execute AI harness to implement the solution
    5. Push changes and create PR
    6. Notify stakeholders

    Example:
        >>> pipeline = AutomationPipeline(config)
        >>> result = pipeline.execute(issue_data, "owner/repo", 123)
        >>> print(result.pr_url)
    """

    def __init__(
        self,
        work_dir: Path,
        github_token: str,
        webhook_secret: Optional[str] = None,
        iflow_path: Optional[str] = None,
        default_reviewers: Optional[List[str]] = None,
    ):
        """
        Initialize the automation pipeline.

        Args:
            work_dir: Working directory for repositories
            github_token: GitHub personal access token
            webhook_secret: Webhook secret for GitHub
            iflow_path: Path to iFlow CLI
            default_reviewers: Default reviewers for PRs
        """
        self.work_dir = Path(work_dir)
        self.github_token = github_token
        self.default_reviewers = default_reviewers or []

        # Initialize components
        self.github_client = GitHubClient(token=github_token)
        self.notifier = Notifier(self.github_client)
        self.issue_parser = IssueParser()
        self.requirement_splitter = RequirementSplitter(iflow_path=iflow_path)
        self.repo_manager = RepositoryManager(
            work_dir=work_dir,
            github_token=github_token,
        )
        self.branch_manager = BranchManager(self.repo_manager)
        self.pr_manager = PRManager(self.github_client)

        self._state = PipelineState.IDLE

    @property
    def state(self) -> PipelineState:
        """Current pipeline state."""
        return self._state

    def execute(
        self,
        issue_data: Dict[str, Any],
        repo: str,
        issue_number: int,
    ) -> PipelineResult:
        """
        Execute the automation pipeline for an issue.

        Args:
            issue_data: Raw issue data from webhook
            repo: Repository name in 'owner/repo' format
            issue_number: Issue number

        Returns:
            PipelineResult with execution details
        """
        logger.info(f"Starting pipeline for issue #{issue_number} in {repo}")

        try:
            # Step 1: Parse and analyze issue
            self._state = PipelineState.ANALYZING
            parsed_issue = self.issue_parser.parse(issue_data)
            
            # Create notification context
            ctx = NotificationContext(
                repo=repo,
                issue_number=issue_number,
            )
            
            # Notify task start
            self.notifier.notify_task_started(ctx)

            # Step 2: Analyze requirements
            analysis = self.requirement_splitter.analyze(parsed_issue)
            logger.info(f"Analysis complete: {len(analysis.tasks)} tasks generated")

            # Step 3: Prepare repository
            self._state = PipelineState.PREPARING_REPO
            repo_info = self.repo_manager.clone_or_fetch(repo)
            logger.info(f"Repository ready at {repo_info.local_path}")

            # Step 4: Create branch
            self._state = PipelineState.CREATING_BRANCH
            branch_name = self.branch_manager.create_branch_for_issue(
                full_name=repo,
                issue_number=issue_number,
                issue_title=parsed_issue.title,
                issue_labels=parsed_issue.labels,
            )
            ctx.branch_name = branch_name
            logger.info(f"Created branch: {branch_name}")

            # Step 5: Generate feature list
            feature_list_path = self.requirement_splitter.generate_feature_list_file(
                result=analysis,
                output_path=repo_info.local_path,
            )
            logger.info(f"Generated feature list at {feature_list_path}")

            # Step 6: Execute AI harness
            self._state = PipelineState.EXECUTING
            execution_result = self._execute_harness(
                repo_path=repo_info.local_path,
                issue_number=issue_number,
            )

            if not execution_result.get("success"):
                return self._handle_failure(
                    ctx=ctx,
                    error=execution_result.get("error", "Harness execution failed"),
                )

            # Step 7: Push changes
            self._state = PipelineState.PUSHING
            self._push_changes(repo, branch_name)

            # Step 8: Create PR
            self._state = PipelineState.CREATING_PR
            pr = self._create_pr(
                repo=repo,
                branch_name=branch_name,
                issue_number=issue_number,
                parsed_issue=parsed_issue,
                analysis=analysis,
            )
            ctx.pr_number = pr.number

            # Step 9: Request review
            if self.default_reviewers:
                self.pr_manager.request_review(
                    repo=repo,
                    pr_number=pr.number,
                    reviewers=self.default_reviewers,
                )

            # Step 10: Notify completion
            self._state = PipelineState.NOTIFYING
            self.notifier.notify_task_completed(ctx, pr.html_url)

            self._state = PipelineState.COMPLETED
            return PipelineResult(
                success=True,
                state=self._state,
                message="Pipeline completed successfully",
                issue_number=issue_number,
                repo=repo,
                branch=branch_name,
                pr_number=pr.number,
                pr_url=pr.html_url,
                data={
                    "analysis": analysis.to_feature_list(),
                },
            )

        except Exception as e:
            logger.exception(f"Pipeline failed: {e}")
            return self._handle_failure(
                ctx=NotificationContext(repo=repo, issue_number=issue_number),
                error=str(e),
            )

    def _execute_harness(
        self,
        repo_path: Path,
        issue_number: int,
    ) -> Dict[str, Any]:
        """Execute the AI harness to implement tasks."""
        import subprocess
        import os

        logger.info(f"Executing harness in {repo_path}")

        # Find iflow_runner.py
        harness_runner = self._find_harness_runner()
        if not harness_runner:
            return {
                "success": False,
                "error": "Could not find iflow_runner.py",
            }

        try:
            # Run the harness
            cmd = [
                "python",
                str(harness_runner),
                "continuous",
                "--project",
                str(repo_path),
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600,  # 1 hour timeout
                cwd=str(repo_path),
            )

            if result.returncode == 0:
                logger.info("Harness execution completed")
                return {"success": True}
            else:
                logger.error(f"Harness failed: {result.stderr}")
                return {
                    "success": False,
                    "error": result.stderr or "Unknown error",
                }

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Harness execution timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _find_harness_runner(self) -> Optional[Path]:
        """Find the iflow_runner.py script."""
        # Check common locations
        possible_paths = [
            self.work_dir.parent / "iflow_runner.py",
            Path(__file__).parent.parent.parent / "iflow_runner.py",
            Path.cwd() / "iflow_runner.py",
        ]

        for path in possible_paths:
            if path.exists():
                return path

        return None

    def _push_changes(self, repo: str, branch_name: str) -> None:
        """Push changes to remote."""
        from git import Repo

        repo_path = self.repo_manager.get_repo_path(repo)
        git_repo = Repo(repo_path)

        # Add all changes
        git_repo.git.add(A=True)

        # Commit if there are changes
        if git_repo.is_dirty():
            git_repo.index.commit("Automated implementation by AI Harness")

        # Push to remote
        origin = git_repo.remote(name="origin")
        origin.push(branch_name)
        logger.info(f"Pushed branch {branch_name} to remote")

    def _create_pr(
        self,
        repo: str,
        branch_name: str,
        issue_number: int,
        parsed_issue: ParsedIssue,
        analysis: AnalysisResult,
    ) -> Any:
        """Create a pull request."""
        # Generate PR title and body
        title = self.pr_manager.generate_pr_title(
            issue_number=issue_number,
            issue_title=parsed_issue.title,
            issue_type=parsed_issue.issue_type.value,
        )

        body = self.pr_manager.generate_pr_body(
            issue_number=issue_number,
            issue_title=parsed_issue.title,
            changes_summary=analysis.overall_approach or "Automated implementation",
            tasks_completed=[t.title for t in analysis.tasks if t.passes],
        )

        pr = self.pr_manager.create_pr(
            repo=repo,
            title=title,
            head=branch_name,
            body=body,
            issue_number=issue_number,
        )

        return pr

    def _handle_failure(
        self,
        ctx: NotificationContext,
        error: str,
    ) -> PipelineResult:
        """Handle pipeline failure."""
        self._state = PipelineState.FAILED
        self.notifier.notify_failure(ctx, error)
        
        return PipelineResult(
            success=False,
            state=self._state,
            message=f"Pipeline failed: {error}",
            issue_number=ctx.issue_number,
            repo=ctx.repo,
            branch=ctx.branch_name,
            error=error,
        )

    def get_status(self) -> Dict[str, Any]:
        """Get pipeline status."""
        return {
            "state": self._state.value,
            "work_dir": str(self.work_dir),
        }

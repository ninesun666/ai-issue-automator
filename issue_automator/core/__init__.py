"""
issue_automator.core - Core scheduling and management primitives.

This module provides the core functionality for the automation pipeline,
including task management, scheduling, and workflow orchestration.
"""

from issue_automator.core.pipeline import AutomationPipeline, PipelineState
from issue_automator.core.task_manager import TaskQueue, Task, TaskStatus
from issue_automator.core.scheduler import TaskScheduler

__all__ = [
    "AutomationPipeline",
    "PipelineState",
    "TaskQueue",
    "Task",
    "TaskStatus",
    "TaskScheduler",
]
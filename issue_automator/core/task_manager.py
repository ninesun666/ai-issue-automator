"""
Task queue management for automation pipeline.

This module provides a serial task queue implementation for
processing issues one at a time.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from queue import Queue
import threading

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Status of a task in the queue."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Task priority levels."""
    CRITICAL = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3


@dataclass
class Task:
    """A task in the automation queue."""
    id: str
    issue_number: int
    repo: str
    title: str
    issue_data: Dict[str, Any]
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    result: Optional[Dict[str, Any]] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "issue_number": self.issue_number,
            "repo": self.repo,
            "title": self.title,
            "priority": self.priority.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
            "result": self.result,
        }


class TaskQueue:
    """
    Serial task queue for processing automation tasks.

    This implementation processes tasks one at a time (serially)
    to avoid conflicts between concurrent operations on the same
    or related repositories.

    Example:
        >>> queue = TaskQueue()
        >>> queue.add_task(task)
        >>> next_task = queue.get_next()
    """

    def __init__(self, max_size: int = 100):
        """
        Initialize the task queue.

        Args:
            max_size: Maximum number of tasks in the queue
        """
        self._queue: Queue = Queue(maxsize=max_size)
        self._tasks: Dict[str, Task] = {}
        self._lock = threading.Lock()
        self._current_task: Optional[Task] = None
        self._counter = 0

    def add_task(
        self,
        issue_number: int,
        repo: str,
        title: str,
        issue_data: Dict[str, Any],
        priority: TaskPriority = TaskPriority.MEDIUM,
    ) -> Task:
        """
        Add a new task to the queue.

        Args:
            issue_number: GitHub issue number
            repo: Repository name
            title: Task title
            issue_data: Raw issue data
            priority: Task priority

        Returns:
            Created Task object
        """
        with self._lock:
            self._counter += 1
            task_id = f"task-{self._counter:04d}"
            
            task = Task(
                id=task_id,
                issue_number=issue_number,
                repo=repo,
                title=title,
                issue_data=issue_data,
                priority=priority,
            )
            
            self._tasks[task_id] = task
            self._queue.put(task)
            
            logger.info(f"Added task {task_id}: Issue #{issue_number} in {repo}")
            return task

    def get_next(self) -> Optional[Task]:
        """
        Get the next task from the queue.

        Returns:
            Next Task to process, or None if queue is empty
        """
        try:
            task = self._queue.get_nowait()
            with self._lock:
                self._current_task = task
                task.status = TaskStatus.RUNNING
                task.started_at = datetime.now()
            logger.info(f"Retrieved task {task.id} for processing")
            return task
        except:
            return None

    def complete_task(
        self,
        task_id: str,
        result: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Mark a task as completed."""
        with self._lock:
            if task_id in self._tasks:
                task = self._tasks[task_id]
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now()
                task.result = result
                
                if self._current_task and self._current_task.id == task_id:
                    self._current_task = None
                
                logger.info(f"Completed task {task_id}")

    def fail_task(
        self,
        task_id: str,
        error: str,
    ) -> None:
        """Mark a task as failed."""
        with self._lock:
            if task_id in self._tasks:
                task = self._tasks[task_id]
                task.status = TaskStatus.FAILED
                task.completed_at = datetime.now()
                task.error = error
                
                if self._current_task and self._current_task.id == task_id:
                    self._current_task = None
                
                logger.error(f"Failed task {task_id}: {error}")

    def cancel_task(self, task_id: str) -> None:
        """Cancel a pending task."""
        with self._lock:
            if task_id in self._tasks:
                task = self._tasks[task_id]
                if task.status == TaskStatus.PENDING:
                    task.status = TaskStatus.CANCELLED
                    logger.info(f"Cancelled task {task_id}")

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        return self._tasks.get(task_id)

    def get_current_task(self) -> Optional[Task]:
        """Get the currently running task."""
        with self._lock:
            return self._current_task

    def get_pending_count(self) -> int:
        """Get number of pending tasks."""
        return self._queue.qsize()

    def get_all_tasks(self) -> List[Task]:
        """Get all tasks."""
        return list(self._tasks.values())

    def get_tasks_by_status(self, status: TaskStatus) -> List[Task]:
        """Get tasks filtered by status."""
        return [t for t in self._tasks.values() if t.status == status]

    def clear_completed(self) -> int:
        """Remove completed tasks from history. Returns count removed."""
        with self._lock:
            to_remove = [
                tid for tid, t in self._tasks.items()
                if t.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED)
            ]
            for tid in to_remove:
                del self._tasks[tid]
            logger.info(f"Cleared {len(to_remove)} completed tasks")
            return len(to_remove)

    def is_empty(self) -> bool:
        """Check if queue is empty."""
        return self._queue.empty()

    def is_busy(self) -> bool:
        """Check if a task is currently running."""
        with self._lock:
            return self._current_task is not None

    def get_status(self) -> Dict[str, Any]:
        """Get queue status summary."""
        with self._lock:
            status_counts = {}
            for status in TaskStatus:
                status_counts[status.value] = len([
                    t for t in self._tasks.values() if t.status == status
                ])
            
            return {
                "total_tasks": len(self._tasks),
                "pending": self._queue.qsize(),
                "current_task": self._current_task.id if self._current_task else None,
                "status_counts": status_counts,
            }

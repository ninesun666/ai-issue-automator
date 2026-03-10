"""
Task scheduler for automation pipeline.

This module provides a scheduler that processes tasks from the queue
and executes them using the automation pipeline.
"""

import logging
import threading
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

from issue_automator.core.task_manager import TaskQueue, TaskStatus

logger = logging.getLogger(__name__)


@dataclass
class SchedulerConfig:
    """Configuration for the task scheduler."""
    poll_interval: float = 5.0  # Seconds between queue polls
    max_retries: int = 3
    retry_delay: float = 10.0  # Seconds before retry
    task_timeout: int = 3600  # Seconds before task timeout


class TaskScheduler:
    """
    Scheduler that processes tasks from the queue.

    This scheduler runs in a background thread and processes
    tasks serially from the task queue.

    Example:
        >>> scheduler = TaskScheduler(queue, pipeline)
        >>> scheduler.start()
        >>> # ... tasks are processed in background
        >>> scheduler.stop()
    """

    def __init__(
        self,
        task_queue: TaskQueue,
        pipeline,  # AutomationPipeline
        config: Optional[SchedulerConfig] = None,
    ):
        """
        Initialize the scheduler.

        Args:
            task_queue: TaskQueue instance
            pipeline: AutomationPipeline instance
            config: Scheduler configuration
        """
        self.queue = task_queue
        self.pipeline = pipeline
        self.config = config or SchedulerConfig()

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def start(self) -> None:
        """Start the scheduler."""
        if self._running:
            logger.warning("Scheduler is already running")
            return

        self._running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info("Task scheduler started")

    def stop(self) -> None:
        """Stop the scheduler."""
        if not self._running:
            return

        self._running = False
        self._stop_event.set()
        
        if self._thread:
            self._thread.join(timeout=10)
            self._thread = None
        
        logger.info("Task scheduler stopped")

    def _run_loop(self) -> None:
        """Main scheduler loop."""
        logger.info("Scheduler loop started")

        while self._running and not self._stop_event.is_set():
            try:
                # Check if we can process a task
                if not self.queue.is_busy():
                    task = self.queue.get_next()
                    if task:
                        self._process_task(task)

                # Wait before next poll
                self._stop_event.wait(self.config.poll_interval)

            except Exception as e:
                logger.exception(f"Error in scheduler loop: {e}")
                self._stop_event.wait(self.config.retry_delay)

        logger.info("Scheduler loop ended")

    def _process_task(self, task) -> None:
        """Process a single task."""
        logger.info(f"Processing task {task.id}: Issue #{task.issue_number}")

        retry_count = 0
        last_error = None

        while retry_count < self.config.max_retries:
            try:
                # Execute the pipeline for this task
                result = self.pipeline.execute(
                    issue_data=task.issue_data,
                    repo=task.repo,
                    issue_number=task.issue_number,
                )

                if result.get("success"):
                    self.queue.complete_task(task.id, result)
                    return
                else:
                    last_error = result.get("error", "Unknown error")
                    logger.warning(
                        f"Task {task.id} failed (attempt {retry_count + 1}): {last_error}"
                    )

            except Exception as e:
                last_error = str(e)
                logger.exception(f"Exception processing task {task.id}")

            retry_count += 1
            if retry_count < self.config.max_retries:
                logger.info(f"Retrying task {task.id} in {self.config.retry_delay}s")
                self._stop_event.wait(self.config.retry_delay)

        # All retries exhausted
        self.queue.fail_task(task.id, last_error or "Max retries exceeded")

    def is_running(self) -> bool:
        """Check if scheduler is running."""
        return self._running

    def get_status(self) -> Dict[str, Any]:
        """Get scheduler status."""
        return {
            "running": self._running,
            "queue_status": self.queue.get_status(),
            "config": {
                "poll_interval": self.config.poll_interval,
                "max_retries": self.config.max_retries,
                "retry_delay": self.config.retry_delay,
            },
        }

    def process_now(self) -> Optional[Dict[str, Any]]:
        """
        Immediately process the next task (blocking).

        Returns:
            Task result or None if no task available
        """
        if self.queue.is_busy():
            logger.warning("A task is already in progress")
            return None

        task = self.queue.get_next()
        if not task:
            return None

        self._process_task(task)
        return task.result

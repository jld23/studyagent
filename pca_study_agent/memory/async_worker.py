"""Async Memory Operations & Background Consolidation Worker.

Executes expensive memory persistence, spaced repetition calculations, and
mastery analytics consolidation in non-blocking background tasks to prevent
UI latency or chat thread blocking.
"""

from __future__ import annotations

import asyncio
from typing import Any, Callable, Coroutine, Dict, List, Optional
from pca_study_agent.observability.logger import logger


class AsyncMemoryWorker:
    """Manages asynchronous background tasks for memory and analytics consolidation."""

    def __init__(self) -> None:
        self._background_tasks: List[asyncio.Task[Any]] = []

    def schedule_task(
        self,
        task_coro: Coroutine[Any, Any, Any],
        task_name: str = "memory_operation",
    ) -> asyncio.Task[Any]:
        """Schedule a background coroutine without blocking the current execution.

        Args:
            task_coro (Coroutine): The async function to execute.
            task_name (str): Human-readable name of the operation.

        Returns:
            asyncio.Task: The spawned background task.
        """
        try:
            loop = asyncio.get_running_loop()
            task = loop.create_task(task_coro, name=task_name)
            self._background_tasks.append(task)
            # Add cleanup callback
            task.add_done_callback(lambda t: self._on_task_completed(t, task_name))
            return task
        except RuntimeError:
            # Fallback if no event loop is currently active (e.g. during sync unit tests)
            asyncio.run(task_coro)
            return None  # type: ignore

    def _on_task_completed(self, task: asyncio.Task[Any], task_name: str) -> None:
        """Handle background task completion and log errors if any."""
        if task in self._background_tasks:
            self._background_tasks.remove(task)
        if not task.cancelled() and task.exception():
            logger.error(
                "Async background memory operation failed",
                task_name=task_name,
                error=str(task.exception()),
            )
        else:
            logger.debug(
                "Async background memory operation completed successfully",
                task_name=task_name,
            )

    async def wait_all_pending(self, timeout_seconds: float = 5.0) -> None:
        """Wait for all pending memory background tasks to finish."""
        if self._background_tasks:
            await asyncio.wait(self._background_tasks, timeout=timeout_seconds)


# Global async memory worker
async_memory_worker = AsyncMemoryWorker()

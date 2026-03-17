from datetime import datetime, timezone
from typing import Callable

from models.task import TaskStatus


class TaskManager:
    def __init__(self):
        self.tasks: dict[str, TaskStatus] = {}

    def create(self, task_id: str, task_type: str) -> TaskStatus:
        task = TaskStatus(id=task_id, type=task_type, status="queued")
        self.tasks[task_id] = task
        return task

    def get(self, task_id: str) -> TaskStatus:
        if task_id not in self.tasks:
            raise KeyError("Task not found")
        return self.tasks[task_id]

    async def run(self, task_id: str, fn: Callable[[TaskStatus], dict]):
        task = self.get(task_id)
        task.status = "running"
        try:
            result = fn(task)
            task.status = "complete"
            task.progress = 1.0
            task.completed_at = datetime.now(timezone.utc)
            task.result = result
        except Exception as exc:
            task.status = "error"
            task.error = str(exc)
            task.completed_at = datetime.now(timezone.utc)

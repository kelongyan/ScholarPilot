"""RQ worker entry point.

Run with::

    uv run rq worker --url "redis://localhost:6379/0" default

This module exists so the worker can also be started as a Python entry point
and so the task functions are importable by name (RQ resolves
``app.workers.tasks.process_document`` from the queue).
"""

from __future__ import annotations

from rq import Worker

from app.core.config import get_settings
from app.core.redis import redis_client

settings = get_settings()


def run_worker() -> None:
    """Start an RQ worker listening on the configured queue."""
    worker = Worker(
        queues=[settings.rq_queue_name],
        connection=redis_client,
    )
    worker.work()


if __name__ == "__main__":
    run_worker()

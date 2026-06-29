"""Redis connection and RQ queue."""

from __future__ import annotations

from redis import Redis
from rq import Queue

from app.core.config import get_settings

settings = get_settings()

redis_client = Redis.from_url(settings.redis_url, decode_responses=False)


def get_queue() -> Queue:
    """Return the default RQ queue."""
    return Queue(name=settings.rq_queue_name, connection=redis_client)

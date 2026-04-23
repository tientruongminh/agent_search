from __future__ import annotations

import dramatiq
from dramatiq.brokers.redis import RedisBroker
from dramatiq.brokers.stub import StubBroker

from app.core.config import settings

if settings.broker_mode.lower() == "redis":
    broker = RedisBroker(url=settings.redis_url)
else:
    broker = StubBroker()

dramatiq.set_broker(broker)


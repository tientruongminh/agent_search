from __future__ import annotations

from collections import Counter
from threading import Lock

_COUNTERS: Counter[str] = Counter()
_LOCK = Lock()


def increment_metric(name: str, amount: int = 1) -> None:
    with _LOCK:
        _COUNTERS[name] += amount


def metrics_snapshot() -> dict[str, int]:
    with _LOCK:
        return dict(_COUNTERS)


def metrics_text() -> str:
    lines = ["# TYPE agent_search_counter counter"]
    snapshot = metrics_snapshot()
    for key in sorted(snapshot):
        lines.append(f'agent_search_counter{{name="{key}"}} {snapshot[key]}')
    return "\n".join(lines) + "\n"


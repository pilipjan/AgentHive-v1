"""In-Memory Sliding Window Rate Limiter for request and cost protection."""

import time
from collections import defaultdict
from typing import Dict, List, Optional, Tuple


class RateLimiter:
    """Sliding-window rate limiter preventing excessive agent spam and resource exhaustion."""

    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._history: Dict[str, List[float]] = defaultdict(list)

    def is_allowed(self, key: str) -> Tuple[bool, int]:
        """Check if request for key is permitted under rate limit window."""
        now = time.time()
        cutoff = now - self.window_seconds

        # Evict timestamps older than window
        timestamps = [t for t in self._history[key] if t > cutoff]
        self._history[key] = timestamps

        if len(timestamps) >= self.max_requests:
            remaining_seconds = int(self.window_seconds - (now - timestamps[0]))
            return False, max(1, remaining_seconds)

        self._history[key].append(now)
        return True, 0

    def reset(self, key: Optional[str] = None):
        """Reset rate limit history for a key or all keys."""
        if key:
            self._history.pop(key, None)
        else:
            self._history.clear()

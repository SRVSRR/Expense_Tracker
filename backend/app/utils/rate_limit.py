"""Rate limiter configuration."""
import os
from slowapi import Limiter
from slowapi.util import get_remote_address

# Disable rate limiting in test environments
if os.getenv("TESTING") == "1":
    class NoOpLimiter:
        def limit(self, *args, **kwargs):
            def decorator(func):
                return func
            return decorator
        def hit(self, *args, **kwargs):
            pass
    limiter = NoOpLimiter()
else:
    limiter = Limiter(key_func=get_remote_address, default_limits=[])
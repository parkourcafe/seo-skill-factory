from __future__ import annotations

import logging
import time
from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, TypeVar


P = ParamSpec("P")
R = TypeVar("R")


def retry(
    attempts: int = 4,
    initial_delay: float = 1,
    backoff: float = 2,
    retry_exceptions: tuple[type[BaseException], ...] = (Exception,),
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            delay = initial_delay
            last_error: BaseException | None = None
            logger = logging.getLogger(func.__module__)
            for attempt in range(1, attempts + 1):
                try:
                    return func(*args, **kwargs)
                except retry_exceptions as exc:
                    last_error = exc
                    if attempt == attempts:
                        break
                    logger.warning("Retrying %s after error on attempt %s/%s: %s", func.__name__, attempt, attempts, exc)
                    time.sleep(delay)
                    delay *= backoff
            assert last_error is not None
            raise last_error

        return wrapper

    return decorator


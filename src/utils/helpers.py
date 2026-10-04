"""
src/utils/helpers.py
Shared utility functions.
"""
import time
import logging
import functools
from typing import Dict
import numpy as np


def normalize_scores(scores: Dict[int, float]) -> Dict[int, float]:
    """Min-max normalise a dictionary of {id: score} to [0, 1]."""
    if not scores:
        return {}
    values = np.array(list(scores.values()), dtype=float)
    min_v, max_v = values.min(), values.max()
    if max_v == min_v:
        return {k: 0.5 for k in scores}
    return {k: float((v - min_v) / (max_v - min_v)) for k, v in scores.items()}


def timer_decorator(func):
    """Decorator that logs execution time of a function."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        logging.getLogger(func.__module__).debug(
            f"{func.__qualname__} took {elapsed:.3f}s"
        )
        return result
    return wrapper


def setup_logging(level: int = logging.INFO):
    """Configure root logger with a simple format."""
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(name)s – %(message)s",
        datefmt="%H:%M:%S",
        level=level,
    )

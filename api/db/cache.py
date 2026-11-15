"""Small in-process caches, so a request does not pay a network round trip for data that changes only when the
pipeline reloads. The database is remote (about 0.2 s per query), so an endpoint that runs three queries costs
most of a second before it does any work."""
from __future__ import annotations

import functools
import threading
import time
from collections import OrderedDict
from collections.abc import Callable
from typing import Any

DEFAULT_TTL_SECONDS = 300


def ttl_cached(ttl: float = DEFAULT_TTL_SECONDS, max_entries: int = 256) -> Callable:
    """Cache a method's result per (arguments) for `ttl` seconds. Only for read-only lookups.

    Concurrent first calls for the same arguments run once: the others wait for it. Failures are not cached.
    The cache belongs to the instance, so two repositories never share entries.
    """

    def decorate(method: Callable) -> Callable:
        @functools.wraps(method)
        def wrapper(self, *args: Any):
            store: OrderedDict = self.__dict__.setdefault("_ttl_store", OrderedDict())
            lock: threading.Lock = self.__dict__.setdefault("_ttl_lock", threading.Lock())
            key = (method.__name__, args)
            with lock:
                hit = store.get(key)
                if hit and hit[0] > time.monotonic():
                    store.move_to_end(key)
                    return hit[1]
                key_lock = self.__dict__.setdefault("_ttl_key_locks", {}).setdefault(key, threading.Lock())
            with key_lock:
                with lock:
                    hit = store.get(key)
                    if hit and hit[0] > time.monotonic():
                        return hit[1]
                value = method(self, *args)
                with lock:
                    store[key] = (time.monotonic() + ttl, value)
                    while len(store) > max_entries:
                        store.popitem(last=False)
                return value

        return wrapper

    return decorate

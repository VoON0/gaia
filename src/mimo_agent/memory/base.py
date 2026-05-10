"""Base memory classes for session and persistent storage."""

from typing import Any
from datetime import datetime


class MemoryBase:
    """Base class for memory storage."""
    
    def store(self, key: str, value: Any):
        raise NotImplementedError
    
    def retrieve(self, key: str) -> Any | None:
        raise NotImplementedError
    
    def clear(self):
        raise NotImplementedError


class SessionMemory(MemoryBase):
    """In-memory session storage."""
    
    def __init__(self):
        self._data = {}
        self._history = []
    
    def store(self, key: str, value: Any):
        self._data[key] = value
        self._history.append({
            "timestamp": datetime.now().isoformat(),
            "key": key,
            "action": "store"
        })
    
    def retrieve(self, key: str) -> Any | None:
        return self._data.get(key)
    
    def get_history(self, limit: int = 10) -> list[dict]:
        return self._history[-limit:]
    
    def clear(self):
        self._data.clear()
        self._history.clear()

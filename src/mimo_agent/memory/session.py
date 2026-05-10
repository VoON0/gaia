"""Session memory management for agent conversations."""

from .base import SessionMemory

_default_memory = SessionMemory()


def get_memory() -> SessionMemory:
    """Get the default session memory instance."""
    return _default_memory


def reset_memory():
    """Reset the session memory."""
    global _default_memory
    _default_memory = SessionMemory()

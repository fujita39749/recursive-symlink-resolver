"""recursive-symlink-resolver package."""
from .core import resolve, ResolutionError

__all__ = ["resolve", "ResolutionError"]

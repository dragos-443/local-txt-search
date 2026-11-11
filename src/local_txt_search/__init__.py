"""Local text search package."""

from .indexing import IndexBuildError, IndexStats, SkipReason, SkippedFile, rebuild_index


__version__ = "0.1.0"

__all__ = [
    "IndexBuildError",
    "IndexStats",
    "SkipReason",
    "SkippedFile",
    "rebuild_index",
]

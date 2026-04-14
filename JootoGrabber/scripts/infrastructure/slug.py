from __future__ import annotations

import re

_UNSAFE = re.compile(r"[^0-9A-Za-z\u3040-\u30ff\u4e00-\u9fff_-]+")


def board_slug(board_id: int, title: str) -> str:
    """Build a filesystem-safe directory name for a board.

    Format: ``{id}_{sanitized_title}`` (trailing ``_`` stripped when title is empty).
    """
    safe_title = _UNSAFE.sub("_", title).strip("_")
    return f"{board_id}_{safe_title}" if safe_title else str(board_id)

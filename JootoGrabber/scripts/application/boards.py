from __future__ import annotations

from typing import Any

from infrastructure.jooto_client import JootoClient
from infrastructure.paginator import iter_paginated


def list_boards(
    client: JootoClient, include_archived: bool = False
) -> list[dict[str, Any]]:
    """Return all boards accessible to the API key, filtered by archived flag."""
    boards = list(iter_paginated(client, "/v1/boards", items_key="boards"))
    if include_archived:
        return boards
    return [b for b in boards if not b.get("archived")]

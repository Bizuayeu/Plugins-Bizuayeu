from __future__ import annotations

from pathlib import Path
from typing import Any

from infrastructure.jooto_client import JootoClient
from infrastructure.paginator import iter_paginated
from infrastructure.slug import board_slug
from infrastructure.storage import write_json


def backup_board(
    client: JootoClient,
    board: dict[str, Any],
    *,
    output_root: Path,
) -> dict[str, Any]:
    """Fetch and persist tasks / lists / categories for a single board.

    Output layout::
        {output_root}/{slug}/board.json
        {output_root}/{slug}/tasks.json
        {output_root}/{slug}/lists.json
        {output_root}/{slug}/categories.json
    """
    board_id = int(board["id"])
    board_dir = output_root / board_slug(board_id, str(board.get("title", "")))

    tasks = list(iter_paginated(client, f"/v1/boards/{board_id}/tasks", items_key="tasks"))
    lists_ = list(iter_paginated(client, f"/v1/boards/{board_id}/lists", items_key="lists"))
    categories = list(
        iter_paginated(client, f"/v1/boards/{board_id}/categories", items_key="categories")
    )

    write_json(board_dir / "board.json", board)
    write_json(board_dir / "tasks.json", tasks)
    write_json(board_dir / "lists.json", lists_)
    write_json(board_dir / "categories.json", categories)

    return {
        "board_id": board_id,
        "title": board.get("title"),
        "path": str(board_dir),
        "tasks_count": len(tasks),
        "lists_count": len(lists_),
        "categories_count": len(categories),
    }

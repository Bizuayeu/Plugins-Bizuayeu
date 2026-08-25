from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from infrastructure.jooto_client import JootoClient


def iter_paginated(
    client: JootoClient,
    path: str,
    *,
    items_key: str,
    per_page: int = 100,
) -> Iterator[dict[str, Any]]:
    """Iterate items across all pages of a Jooto paginated endpoint.

    Jooto paginated responses share the shape:
        {"<items_key>": [...], "page": N, "per_page": M, "total": X, "total_pages": Y}

    The caller may include query params in ``path``; ``per_page`` and ``page`` are appended.
    """
    sep = "&" if "?" in path else "?"
    page = 1
    while True:
        url = f"{path}{sep}per_page={per_page}&page={page}"
        body = client.get(url)
        if not isinstance(body, dict):
            return

        yield from body.get(items_key, [])

        total_pages = int(body.get("total_pages", 0))
        if page >= total_pages:
            return
        page += 1

from __future__ import annotations

import json
from pathlib import Path

from infrastructure.storage import write_json


def load_sync_state(path: Path) -> dict[str, str]:
    """Return {board_id_str: updated_at_iso}. Empty dict if missing or corrupt."""
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return {str(k): str(v) for k, v in data.items()}
        return {}
    except (json.JSONDecodeError, OSError):
        return {}


def save_sync_state(path: Path, state: dict[str, str]) -> None:
    write_json(path, state)

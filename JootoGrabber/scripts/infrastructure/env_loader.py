from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path


def load_env(dotenv_path: Path | None = None) -> Mapping[str, str]:
    """Merge os.environ with a simple KEY=VALUE .env file if present.

    os.environ takes precedence so real env can override.
    """
    merged: dict[str, str] = {}
    if dotenv_path is not None and dotenv_path.exists():
        merged.update(_parse_dotenv(dotenv_path.read_text(encoding="utf-8")))
    for key, value in os.environ.items():
        merged[key] = value
    return merged


def _parse_dotenv(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            out[key] = value
    return out

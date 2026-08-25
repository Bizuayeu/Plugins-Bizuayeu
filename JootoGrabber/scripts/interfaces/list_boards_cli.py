from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from application.boards import list_boards
from infrastructure.config import ConfigError, load_config
from infrastructure.env_loader import load_env
from infrastructure.jooto_client import JootoClient, JootoError
from infrastructure.urllib_transport import UrllibTransport


def _build_client() -> JootoClient:
    env = load_env(dotenv_path=Path(__file__).resolve().parents[2] / ".env")
    return JootoClient(load_config(env), transport=UrllibTransport())


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="List Jooto boards accessible to the API key.")
    parser.add_argument("--include-archived", action="store_true")
    args = parser.parse_args(argv)

    try:
        client = _build_client()
    except ConfigError as e:
        print(json.dumps({"status": "error", "reason": "config_error", "message": str(e)}))
        return 2

    try:
        boards = list_boards(client, include_archived=args.include_archived)
    except JootoError as e:
        print(json.dumps({"status": "error", "reason": "api_error", "message": str(e)}))
        return 1

    summary = [
        {
            "id": b["id"],
            "title": b.get("title", ""),
            "archived": bool(b.get("archived")),
            "updated_at": b.get("updated_at"),
        }
        for b in boards
    ]
    print(
        json.dumps({"status": "ok", "count": len(summary), "boards": summary}, ensure_ascii=False)
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

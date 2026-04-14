from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

from application.backup import backup_board
from application.boards import list_boards
from infrastructure.config import ConfigError, load_config
from infrastructure.env_loader import load_env
from infrastructure.jooto_client import JootoClient, JootoError
from infrastructure.urllib_transport import UrllibTransport


def _build_client() -> JootoClient:
    env = load_env(dotenv_path=Path(__file__).resolve().parents[2] / ".env")
    return JootoClient(load_config(env), transport=UrllibTransport())


def _fetch_board(client: JootoClient, board_id: int) -> dict[str, Any]:
    body = client.get(f"/v1/boards/{board_id}")
    if not isinstance(body, dict):
        raise JootoError(f"unexpected board response for id={board_id}")
    return body


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Back up Jooto board(s) to JSON files.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--board", type=int, help="Specific board id to back up")
    group.add_argument("--all-active", action="store_true", help="Back up every non-archived board")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/jooto"),
        help="Output root directory (default: data/jooto)",
    )
    args = parser.parse_args(argv)

    try:
        client = _build_client()
    except ConfigError as e:
        print(json.dumps({"status": "error", "reason": "config_error", "message": str(e)}))
        return 2

    try:
        if args.board is not None:
            board = _fetch_board(client, args.board)
            boards = [board]
        else:
            boards = list_boards(client, include_archived=False)

        results = [backup_board(client, b, output_root=args.output) for b in boards]
    except JootoError as e:
        print(json.dumps({"status": "error", "reason": "api_error", "message": str(e)}))
        return 1

    print(
        json.dumps(
            {"status": "ok", "boards_backed_up": len(results), "results": results},
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

from application.backup import backup_board, should_skip
from application.boards import list_boards
from infrastructure.config import ConfigError, load_config
from infrastructure.env_loader import load_env
from infrastructure.jooto_client import JootoClient, JootoError
from infrastructure.sync_state import load_sync_state, save_sync_state
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
    parser.add_argument(
        "--force",
        action="store_true",
        help="Ignore sync_state and refetch every board",
    )
    args = parser.parse_args(argv)

    try:
        client = _build_client()
    except ConfigError as e:
        print(json.dumps({"status": "error", "reason": "config_error", "message": str(e)}))
        return 2

    sync_state_path = args.output / "_sync_state.json"
    sync_state = {} if args.force else load_sync_state(sync_state_path)

    try:
        if args.board is not None:
            boards = [_fetch_board(client, args.board)]
        else:
            boards = list_boards(client, include_archived=False)

        results: list[dict[str, Any]] = []
        skipped: list[dict[str, Any]] = []
        for b in boards:
            if should_skip(b, sync_state=sync_state):
                skipped.append({"board_id": int(b["id"]), "title": b.get("title")})
                continue
            results.append(backup_board(client, b, output_root=args.output))
            sync_state[str(b["id"])] = str(b.get("updated_at", ""))

        save_sync_state(sync_state_path, sync_state)
    except JootoError as e:
        print(json.dumps({"status": "error", "reason": "api_error", "message": str(e)}))
        return 1

    print(
        json.dumps(
            {
                "status": "ok",
                "boards_backed_up": len(results),
                "boards_skipped": len(skipped),
                "results": results,
                "skipped": skipped,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

import json
from pathlib import Path
from typing import Any

from application.backup import backup_board
from infrastructure.config import Config
from infrastructure.jooto_client import HttpResponse, JootoClient


class _Transport:
    def __init__(self, responses: dict[str, Any]) -> None:
        self._responses = responses
        self.calls: list[str] = []

    def get(self, url: str, headers: dict[str, str]) -> HttpResponse:
        self.calls.append(url)
        for key, body in self._responses.items():
            if key in url:
                return HttpResponse(status=200, body=body)
        raise AssertionError(f"unexpected url: {url}")


def _single_page(items_key: str, items: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        items_key: items,
        "page": 1,
        "per_page": 100,
        "total": len(items),
        "total_pages": 1,
    }


class TestBackupBoard:
    def test_writes_expected_files(self, tmp_path: Path) -> None:
        board = {
            "id": 42,
            "title": "足立六町",
            "archived": False,
            "updated_at": "2026-04-14",
        }
        transport = _Transport(
            {
                "/v1/boards/42/tasks": _single_page("tasks", [{"id": 1, "title": "t"}]),
                "/v1/boards/42/lists": _single_page(
                    "lists", [{"id": 10, "title": "ToDo"}]
                ),
                "/v1/boards/42/categories": _single_page("categories", [{"id": 99}]),
            }
        )
        client = JootoClient(Config(api_key="k"), transport)

        result = backup_board(client, board, output_root=tmp_path)

        board_dir = tmp_path / "42_足立六町"
        assert (board_dir / "board.json").exists()
        assert (
            json.loads((board_dir / "board.json").read_text(encoding="utf-8"))["id"]
            == 42
        )
        assert json.loads((board_dir / "tasks.json").read_text(encoding="utf-8")) == [
            {"id": 1, "title": "t"}
        ]
        assert (
            json.loads((board_dir / "lists.json").read_text(encoding="utf-8"))[0]["id"]
            == 10
        )
        assert (
            json.loads((board_dir / "categories.json").read_text(encoding="utf-8"))[0][
                "id"
            ]
            == 99
        )

        assert result["board_id"] == 42
        assert result["tasks_count"] == 1
        assert result["path"] == str(board_dir)

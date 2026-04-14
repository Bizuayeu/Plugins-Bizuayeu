from typing import Any

from application.boards import list_boards
from infrastructure.config import Config
from infrastructure.jooto_client import HttpResponse, JootoClient


class _Transport:
    def __init__(self, pages: list[dict[str, Any]]) -> None:
        self._pages = pages
        self.calls: list[str] = []

    def get(self, url: str, headers: dict[str, str]) -> HttpResponse:
        self.calls.append(url)
        idx = len(self.calls) - 1
        return HttpResponse(status=200, body=self._pages[idx])


def _client(pages: list[dict[str, Any]]) -> JootoClient:
    return JootoClient(Config(api_key="k"), _Transport(pages))


class TestListBoards:
    def test_filters_archived_by_default(self) -> None:
        client = _client(
            [
                {
                    "boards": [
                        {"id": 1, "title": "A", "archived": False},
                        {"id": 2, "title": "B", "archived": True},
                    ],
                    "page": 1,
                    "per_page": 100,
                    "total": 2,
                    "total_pages": 1,
                }
            ]
        )
        result = list_boards(client)
        assert [b["id"] for b in result] == [1]

    def test_include_archived(self) -> None:
        client = _client(
            [
                {
                    "boards": [
                        {"id": 1, "archived": False},
                        {"id": 2, "archived": True},
                    ],
                    "page": 1,
                    "per_page": 100,
                    "total": 2,
                    "total_pages": 1,
                }
            ]
        )
        result = list_boards(client, include_archived=True)
        assert [b["id"] for b in result] == [1, 2]

import pytest

from infrastructure.config import Config
from infrastructure.jooto_client import JootoClient
from infrastructure.paginator import iter_paginated


class _FakeTransport:
    """Returns canned responses by URL, recording calls."""

    def __init__(self, responses: dict[str, object]) -> None:
        self._responses = responses
        self.calls: list[str] = []

    def get(self, url: str, headers: dict[str, str]):  # type: ignore[no-untyped-def]
        from infrastructure.jooto_client import HttpResponse

        self.calls.append(url)
        if url not in self._responses:
            raise AssertionError(f"unexpected URL: {url}")
        return HttpResponse(status=200, body=self._responses[url])


def _client(responses: dict[str, object]) -> tuple[JootoClient, _FakeTransport]:
    t = _FakeTransport(responses)
    return JootoClient(Config(api_key="k", base_url="https://api.jooto.com"), t), t


class TestIterPaginated:
    def test_single_page(self) -> None:
        client, t = _client(
            {
                "https://api.jooto.com/v1/boards?per_page=100&page=1": {
                    "boards": [{"id": 1}, {"id": 2}],
                    "page": 1,
                    "per_page": 100,
                    "total": 2,
                    "total_pages": 1,
                }
            }
        )
        items = list(iter_paginated(client, "/v1/boards", items_key="boards", per_page=100))
        assert items == [{"id": 1}, {"id": 2}]
        assert len(t.calls) == 1

    def test_multi_page(self) -> None:
        client, t = _client(
            {
                "https://api.jooto.com/v1/boards?per_page=2&page=1": {
                    "boards": [{"id": 1}, {"id": 2}],
                    "page": 1,
                    "per_page": 2,
                    "total": 3,
                    "total_pages": 2,
                },
                "https://api.jooto.com/v1/boards?per_page=2&page=2": {
                    "boards": [{"id": 3}],
                    "page": 2,
                    "per_page": 2,
                    "total": 3,
                    "total_pages": 2,
                },
            }
        )
        items = list(iter_paginated(client, "/v1/boards", items_key="boards", per_page=2))
        assert [x["id"] for x in items] == [1, 2, 3]
        assert len(t.calls) == 2

    def test_preserves_existing_query_params(self) -> None:
        client, t = _client(
            {
                "https://api.jooto.com/v1/boards/7/tasks?archived=false&per_page=100&page=1": {
                    "tasks": [],
                    "page": 1,
                    "per_page": 100,
                    "total": 0,
                    "total_pages": 1,
                }
            }
        )
        list(iter_paginated(client, "/v1/boards/7/tasks?archived=false", items_key="tasks"))
        assert "archived=false" in t.calls[0]

    def test_stops_when_total_pages_is_zero(self) -> None:
        client, t = _client(
            {
                "https://api.jooto.com/v1/boards?per_page=100&page=1": {
                    "boards": [],
                    "page": 1,
                    "per_page": 100,
                    "total": 0,
                    "total_pages": 0,
                }
            }
        )
        items = list(iter_paginated(client, "/v1/boards", items_key="boards"))
        assert items == []
        assert len(t.calls) == 1

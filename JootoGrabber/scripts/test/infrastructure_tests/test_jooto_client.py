from dataclasses import dataclass, field
from typing import Any

import pytest

from infrastructure.config import Config
from infrastructure.jooto_client import (
    HttpResponse,
    JootoAuthError,
    JootoClient,
    JootoHttpError,
    JootoRateLimitError,
)


@dataclass
class FakeTransport:
    """Captures the last call; returns a canned response."""

    response: HttpResponse
    last_url: str | None = field(default=None)
    last_headers: dict[str, str] = field(default_factory=dict)

    def get(self, url: str, headers: dict[str, str]) -> HttpResponse:
        self.last_url = url
        self.last_headers = dict(headers)
        return self.response


def _cfg() -> Config:
    return Config(api_key="secret-key", base_url="https://app.jooto.com")


class TestJootoClientGet:
    def test_sends_api_key_header_and_builds_url(self) -> None:
        t = FakeTransport(HttpResponse(status=200, body={"organizations": []}))
        client = JootoClient(_cfg(), transport=t)

        client.get("/organizations")

        assert t.last_url == "https://app.jooto.com/organizations"
        assert t.last_headers["X-Jooto-Api-Key"] == "secret-key"

    def test_returns_parsed_body_on_200(self) -> None:
        t = FakeTransport(HttpResponse(status=200, body={"organizations": [{"id": 1}]}))
        client = JootoClient(_cfg(), transport=t)

        assert client.get("/organizations") == {"organizations": [{"id": 1}]}

    def test_normalises_leading_slash_in_path(self) -> None:
        t = FakeTransport(HttpResponse(status=200, body={}))
        client = JootoClient(_cfg(), transport=t)

        client.get("organizations")  # no leading slash
        assert t.last_url == "https://app.jooto.com/organizations"

    @pytest.mark.parametrize("status", [401, 403])
    def test_auth_status_raises_auth_error(self, status: int) -> None:
        t = FakeTransport(HttpResponse(status=status, body={"message": "nope"}))
        client = JootoClient(_cfg(), transport=t)

        with pytest.raises(JootoAuthError) as exc:
            client.get("/organizations")
        assert exc.value.http_status == status

    def test_429_raises_rate_limit_error(self) -> None:
        t = FakeTransport(HttpResponse(status=429, body={}))
        client = JootoClient(_cfg(), transport=t)

        with pytest.raises(JootoRateLimitError):
            client.get("/organizations")

    def test_other_4xx_5xx_raises_http_error(self) -> None:
        t = FakeTransport(HttpResponse(status=500, body={"message": "boom"}))
        client = JootoClient(_cfg(), transport=t)

        with pytest.raises(JootoHttpError) as exc:
            client.get("/organizations")
        assert exc.value.http_status == 500

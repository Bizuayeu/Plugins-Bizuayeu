import json
from typing import Any

import pytest

from infrastructure.jooto_client import HttpResponse, JootoClient
from interfaces import auth_cli


class _StubTransport:
    def __init__(self, response: HttpResponse) -> None:
        self._response = response
        self.calls: list[tuple[str, dict[str, str]]] = []

    def get(self, url: str, headers: dict[str, str]) -> HttpResponse:
        self.calls.append((url, dict(headers)))
        return self._response


def _make_client(response: HttpResponse) -> tuple[JootoClient, _StubTransport]:
    from infrastructure.config import Config

    t = _StubTransport(response)
    return JootoClient(Config(api_key="k", base_url="https://app.jooto.com"), t), t


class TestRunAuth:
    def test_ok_result(self) -> None:
        client, _ = _make_client(
            HttpResponse(status=200, body={"organizations": [{"id": 1}, {"id": 2}]})
        )
        result = auth_cli.run_auth(client)
        assert result == {
            "status": "ok",
            "base_url": "https://app.jooto.com",
            "organizations_count": 2,
        }

    def test_auth_error_returns_structured_result(self) -> None:
        client, _ = _make_client(HttpResponse(status=401, body={"message": "no"}))
        result = auth_cli.run_auth(client)
        assert result == {
            "status": "error",
            "reason": "unauthorized",
            "http_status": 401,
        }

    def test_rate_limit_result(self) -> None:
        client, _ = _make_client(HttpResponse(status=429, body={}))
        result = auth_cli.run_auth(client)
        assert result["status"] == "error"
        assert result["reason"] == "rate_limited"
        assert result["http_status"] == 429

    def test_organizations_key_missing_counts_zero(self) -> None:
        client, _ = _make_client(HttpResponse(status=200, body={}))
        result = auth_cli.run_auth(client)
        assert result["organizations_count"] == 0


class TestMainCli:
    def test_main_prints_json_and_exits_zero_on_success(
        self, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        client, _ = _make_client(HttpResponse(status=200, body={"organizations": []}))
        monkeypatch.setattr(auth_cli, "_build_client", lambda: client)

        code = auth_cli.main([])

        out = capsys.readouterr().out
        parsed: dict[str, Any] = json.loads(out)
        assert parsed["status"] == "ok"
        assert code == 0

    def test_main_returns_nonzero_on_error(
        self, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        client, _ = _make_client(HttpResponse(status=401, body={}))
        monkeypatch.setattr(auth_cli, "_build_client", lambda: client)

        code = auth_cli.main([])
        parsed = json.loads(capsys.readouterr().out)
        assert parsed["status"] == "error"
        assert code != 0

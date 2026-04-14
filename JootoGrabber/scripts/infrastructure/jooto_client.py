from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from infrastructure.config import Config


@dataclass(frozen=True)
class HttpResponse:
    status: int
    body: Any


class HttpTransport(Protocol):
    def get(self, url: str, headers: dict[str, str]) -> HttpResponse: ...


class JootoError(RuntimeError):
    """Base class for Jooto API errors."""


class JootoHttpError(JootoError):
    def __init__(self, http_status: int, body: Any) -> None:
        super().__init__(f"Jooto API error: HTTP {http_status}")
        self.http_status = http_status
        self.body = body


class JootoAuthError(JootoHttpError):
    """401 / 403 — bad or missing API key."""


class JootoRateLimitError(JootoHttpError):
    """429 — rate limited."""


class JootoClient:
    def __init__(self, config: Config, transport: HttpTransport) -> None:
        self._config = config
        self._transport = transport

    def get(self, path: str) -> Any:
        url = f"{self._config.base_url}/{path.lstrip('/')}"
        headers = {"X-Jooto-Api-Key": self._config.api_key}
        resp = self._transport.get(url, headers)

        if 200 <= resp.status < 300:
            return resp.body
        if resp.status in (401, 403):
            raise JootoAuthError(resp.status, resp.body)
        if resp.status == 429:
            raise JootoRateLimitError(resp.status, resp.body)
        raise JootoHttpError(resp.status, resp.body)

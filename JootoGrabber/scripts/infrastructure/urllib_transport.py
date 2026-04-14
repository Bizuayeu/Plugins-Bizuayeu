from __future__ import annotations

import json
import urllib.error
import urllib.request

from infrastructure.jooto_client import HttpResponse


class UrllibTransport:
    """Minimal stdlib-only HTTP transport for JootoClient."""

    def __init__(self, timeout_sec: float = 30.0) -> None:
        self._timeout = timeout_sec

    def get(self, url: str, headers: dict[str, str]) -> HttpResponse:
        req = urllib.request.Request(url, headers=headers, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                body_bytes = resp.read()
                return HttpResponse(status=resp.status, body=_decode_json(body_bytes))
        except urllib.error.HTTPError as e:
            body_bytes = e.read() if hasattr(e, "read") else b""
            return HttpResponse(status=e.code, body=_decode_json(body_bytes))


def _decode_json(data: bytes) -> object:
    if not data:
        return None
    try:
        return json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {"_raw": data[:200].decode("utf-8", errors="replace")}

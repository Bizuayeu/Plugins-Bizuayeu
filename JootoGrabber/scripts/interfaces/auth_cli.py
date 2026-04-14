from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Sequence

from infrastructure.config import ConfigError, load_config
from infrastructure.env_loader import load_env
from infrastructure.jooto_client import (
    JootoAuthError,
    JootoClient,
    JootoHttpError,
    JootoRateLimitError,
)
from infrastructure.urllib_transport import UrllibTransport


def run_auth(client: JootoClient) -> dict[str, Any]:
    try:
        body = client.get("/organizations")
    except JootoAuthError as e:
        return {"status": "error", "reason": "unauthorized", "http_status": e.http_status}
    except JootoRateLimitError as e:
        return {"status": "error", "reason": "rate_limited", "http_status": e.http_status}
    except JootoHttpError as e:
        return {"status": "error", "reason": "http_error", "http_status": e.http_status}

    orgs = body.get("organizations", []) if isinstance(body, dict) else []
    return {
        "status": "ok",
        "base_url": client._config.base_url,  # noqa: SLF001 — deliberate read of config
        "organizations_count": len(orgs),
    }


def _build_client() -> JootoClient:
    env = load_env(dotenv_path=Path(__file__).resolve().parents[2] / ".env")
    config = load_config(env)
    return JootoClient(config, transport=UrllibTransport())


def main(argv: Sequence[str] | None = None) -> int:
    try:
        client = _build_client()
    except ConfigError as e:
        print(json.dumps({"status": "error", "reason": "config_error", "message": str(e)}))
        return 2

    result = run_auth(client)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

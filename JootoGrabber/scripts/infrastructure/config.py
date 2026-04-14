from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

_DEFAULT_BASE_URL = "https://app.jooto.com"


class ConfigError(ValueError):
    """Raised when required configuration is missing or invalid."""


@dataclass(frozen=True)
class Config:
    api_key: str
    base_url: str = _DEFAULT_BASE_URL


def load_config(env: Mapping[str, str]) -> Config:
    api_key = (env.get("JOOTO_API_KEY") or "").strip()
    if not api_key:
        raise ConfigError("JOOTO_API_KEY is required")

    base_url = (env.get("JOOTO_BASE_URL") or _DEFAULT_BASE_URL).rstrip("/")
    return Config(api_key=api_key, base_url=base_url)

#!/usr/bin/env python3
"""
CLI Helpers
===========

JSON 出力、エラー処理、パス解決等の CLI 共通ヘルパ。
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, NoReturn


def default_config_dir() -> Path:
    """
    GmailGrabber の設定ディレクトリを返す。

    Windows: %APPDATA%/GmailGrabber
    Unix: ~/.config/gmailgrabber
    """
    if sys.platform == "win32":
        base = os.environ.get("APPDATA")
        if base:
            return Path(base) / "GmailGrabber"
    return Path.home() / ".config" / "gmailgrabber"


def print_json(data: dict, indent: int = 2) -> None:
    """JSON を stdout に整形出力"""
    print(json.dumps(data, ensure_ascii=False, indent=indent, default=_json_default))


def print_success(data: dict) -> None:
    payload = {"status": "ok", **data}
    print_json(payload)


def fail(message: str, details: dict | None = None, exit_code: int = 1) -> NoReturn:
    """エラー出力して exit"""
    payload: dict[str, Any] = {"status": "error", "error": message}
    if details:
        payload["details"] = details
    print_json(payload)
    sys.exit(exit_code)


def _json_default(obj: Any) -> Any:
    """json.dumps default: datetime, Path を文字列化"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, Path):
        return str(obj)
    raise TypeError(f"not serializable: {type(obj)}")


__all__ = ["default_config_dir", "fail", "print_json", "print_success"]

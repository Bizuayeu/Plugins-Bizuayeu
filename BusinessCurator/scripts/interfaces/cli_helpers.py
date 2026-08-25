#!/usr/bin/env python3
"""
CLI Helpers
===========

CLI 共通のヘルパー関数群。

設計意図:
- 全 CLI で共通の JSON 出力フォーマットを提供
- output_json: status: ok を含むJSON 出力
- output_error: status: error を含むJSON 出力 + exit code 1
- BusinessCurator の CLI は全て JSON-only 出力（md スキルから安定的にパース可能）

Usage:
    from interfaces.cli_helpers import output_json, output_error

    output_json({"status": "ok", "count": 42})
    output_error("File not found", details={"action": "Run setup"})
"""

import json
import sys
from typing import Any, NoReturn

__all__ = ["output_error", "output_json"]


def output_json(data: Any) -> None:
    """
    JSON形式で標準出力に出力（UTF-8、indent=2）

    Args:
        data: JSON 変換可能な任意の型

    Note:
        ensure_ascii=False で日本語を生のまま出力
    """
    print(json.dumps(data, ensure_ascii=False, indent=2))


def output_error(error: str, details: dict[str, Any] | None = None) -> NoReturn:
    """
    エラー JSON を出力し、exit code 1 で終了

    Args:
        error: エラーメッセージ
        details: 追加の詳細情報（オプション）

    Raises:
        SystemExit: 終了コード 1
    """
    result: dict[str, Any] = {"status": "error", "error": error}
    if details:
        result["details"] = details
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(1)

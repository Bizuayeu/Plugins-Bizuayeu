#!/usr/bin/env python3
"""
File Naming (Pure Functions)
============================

メッセージファイル名生成の純関数群。

設計意図:
- .eml ファイル名: YYYYMMDD_HHMMSS_{gmail_id}.eml（時系列ソート可能）
- .mbox ファイル名: {plan_id}.mbox（計画ごと1ファイル）
- ファイル名サニタイズ（Windows/Unix両対応）
- plan_id 生成: query + account のハッシュ（決定的）
"""

import hashlib
import re
from datetime import datetime
from typing import Final

_INVALID_CHARS: Final[re.Pattern[str]] = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def sanitize_filename(name: str, max_length: int = 200) -> str:
    """
    ファイル名として不正な文字を除去。

    Args:
        name: 元のファイル名（拡張子は呼び出し側で追加）
        max_length: 最大長（デフォルト200、Windows MAX_PATH考慮）

    Returns:
        サニタイズ後のファイル名
    """
    sanitized = _INVALID_CHARS.sub("_", name)
    sanitized = sanitized.strip(". ")
    if not sanitized:
        sanitized = "unnamed"
    return sanitized[:max_length]


def eml_filename(internal_date: datetime, gmail_id: str) -> str:
    """
    .eml ファイル名を生成する。

    フォーマット: YYYYMMDD_HHMMSS_{gmail_id}.eml

    Args:
        internal_date: Gmail サーバー受信日時
        gmail_id: Gmail API message.id

    Returns:
        ファイル名（ディレクトリパスは含まない）

    Example:
        >>> from datetime import datetime
        >>> eml_filename(datetime(2026, 4, 5, 14, 30, 12), "18f3a5b1")
        '20260405_143012_18f3a5b1.eml'
    """
    timestamp = internal_date.strftime("%Y%m%d_%H%M%S")
    safe_id = sanitize_filename(gmail_id, max_length=50)
    return f"{timestamp}_{safe_id}.eml"


def mbox_filename(plan_id: str) -> str:
    """
    .mbox ファイル名を生成する。

    フォーマット: {plan_id}.mbox

    Args:
        plan_id: BackupPlan 識別子

    Returns:
        ファイル名
    """
    safe_id = sanitize_filename(plan_id, max_length=100)
    return f"{safe_id}.mbox"


def build_plan_id(
    account_email: str,
    query_string: str,
    output_format: str,
    timestamp: datetime,
) -> str:
    """
    BackupPlan 識別子を決定的に生成する。

    フォーマット: plan_{YYYYMMDD_HHMMSS}_{hash8}
    hash8 = sha256(account_email + query_string + output_format) の先頭8文字

    Args:
        account_email: 対象アカウント
        query_string: ビルド済み Gmail 検索クエリ
        output_format: "eml" | "mbox"
        timestamp: plan 作成時刻（同じパラメータで時刻違いを区別）

    Returns:
        plan_id 文字列
    """
    hash_source = f"{account_email}|{query_string}|{output_format}".encode()
    hash_hex = hashlib.sha256(hash_source).hexdigest()[:8]
    ts = timestamp.strftime("%Y%m%d_%H%M%S")
    return f"plan_{ts}_{hash_hex}"


__all__ = ["build_plan_id", "eml_filename", "mbox_filename", "sanitize_filename"]

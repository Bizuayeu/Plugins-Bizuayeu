#!/usr/bin/env python3
"""
Multi-User File Naming (Pure Functions)
========================================

複数ユーザー Gmail バックアップの plan ID 生成。

設計意図:
- ユーザーリストの順序に依存しない決定的ハッシュ (sort してから hash)
- 同じユーザー集合 + 同じクエリ = 同じ plan_id = 再開可能
- 単一ユーザー版の build_plan_id() と共存 (別ファイルで依存を切る)
"""

import hashlib
from collections.abc import Sequence
from datetime import datetime


def build_multi_plan_id(
    account_emails: Sequence[str],
    query_string: str,
    output_format: str,
    timestamp: datetime,
) -> str:
    """
    MultiUserBackupPlan 識別子を決定的に生成する。

    フォーマット: multi_plan_{YYYYMMDD_HHMMSS}_{hash10}
    hash10 = sha256(sorted_emails + query + output_format) の先頭10文字

    Args:
        account_emails: 対象ユーザーのメールアドレス列
        query_string: ビルド済み Gmail 検索クエリ
        output_format: "eml" | "mbox"
        timestamp: plan 作成時刻

    Returns:
        multi_plan_id 文字列

    Notes:
        emails は内部で sort してから hash に投入する →
        ["a@x", "b@x"] と ["b@x", "a@x"] は同じ plan_id を生成する
    """
    sorted_emails = sorted(set(account_emails))
    joined = "|".join(sorted_emails)
    hash_source = f"{joined}||{query_string}||{output_format}".encode()
    hash_hex = hashlib.sha256(hash_source).hexdigest()[:10]
    ts = timestamp.strftime("%Y%m%d_%H%M%S")
    return f"multi_plan_{ts}_{hash_hex}"


__all__ = ["build_multi_plan_id"]

#!/usr/bin/env python3
"""
Query Builder (Pure Function)
=============================

SearchQuery → Gmail検索文字列 への変換純関数。

Gmail検索仕様:
- from:ADDR, to:ADDR, subject:KEYWORD, label:NAME
- after:YYYY/MM/DD, before:YYYY/MM/DD
- has:attachment
- クエリは空白区切りAND

設計意図:
- 純関数（副作用なし、外部依存なし、決定的）
- raw_query 指定時は他フィールドを無視（エスケープハッチ）
- テスト容易性を最優先
- Property-based testing で不変量を保証
"""

from domain.constants import GMAIL_QUERY_DATE_FORMAT
from domain.exceptions import QueryBuildError
from domain.types.query import DateRange, SearchQuery


def build_gmail_query(query: SearchQuery) -> str:
    """
    SearchQuery を Gmail 検索クエリ文字列に変換する純関数。

    Args:
        query: ドメイン中立な検索クエリ

    Returns:
        Gmail 検索文字列 (例: "from:user@example.com after:2026/04/01 before:2026/04/12")
        空クエリの場合は空文字列を返す（Gmail API では「全メール」の意味）

    Raises:
        QueryBuildError: date_range の start > end の場合
    """
    # raw_query 指定時は優先
    raw = query.get("raw_query")
    if raw is not None and raw.strip():
        return raw.strip()

    parts: list[str] = []

    from_addr = query.get("from_addr")
    if from_addr:
        parts.append(f"from:{from_addr}")

    to_addr = query.get("to_addr")
    if to_addr:
        parts.append(f"to:{to_addr}")

    subject = query.get("subject")
    if subject:
        # 件名にスペースが含まれる場合はダブルクォート
        if " " in subject:
            parts.append(f'subject:"{subject}"')
        else:
            parts.append(f"subject:{subject}")

    label = query.get("label")
    if label:
        # ラベル名にスペース含む場合はハイフン化（Gmail検索の仕様）
        normalized_label = label.replace(" ", "-")
        parts.append(f"label:{normalized_label}")

    date_range = query.get("date_range")
    if date_range is not None:
        parts.extend(_format_date_range(date_range))

    has_attachment = query.get("has_attachment")
    if has_attachment is True:
        parts.append("has:attachment")

    return " ".join(parts)


def _format_date_range(date_range: DateRange) -> list[str]:
    """
    DateRange を Gmail 検索の after:/before: 列に変換する。

    Gmail検索仕様:
    - after:YYYY/MM/DD は「その日以降」(包括)
    - before:YYYY/MM/DD は「その日より前」(排他)
    """
    start = date_range.get("start")
    end = date_range.get("end")

    if start is not None and end is not None and start > end:
        raise QueryBuildError(f"date_range start ({start}) > end ({end})")

    parts: list[str] = []
    if start is not None:
        parts.append(f"after:{start.strftime(GMAIL_QUERY_DATE_FORMAT)}")
    if end is not None:
        parts.append(f"before:{end.strftime(GMAIL_QUERY_DATE_FORMAT)}")
    return parts


__all__ = ["build_gmail_query"]

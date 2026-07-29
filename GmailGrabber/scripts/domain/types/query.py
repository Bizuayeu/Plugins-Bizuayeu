#!/usr/bin/env python3
"""
Query Domain Types
==================

Gmail検索クエリのドメイン表現。

設計意図:
- SearchQuery はユーザー意図をドメイン中立に表現した中間構造
- Gmail検索文字列への変換は domain/query_builder.py が純関数で担う
- 全フィールドOptional: 空クエリ = "全メール" を許容
- raw_query でエスケープハッチ提供（高度なクエリをそのまま渡す用）

Usage:
    from datetime import date
    from domain.types.query import DateRange, SearchQuery

    q: SearchQuery = {
        "from_addr": "togami-log@meguru-construction.example.jp",
        "to_addr": None,
        "subject": None,
        "label": None,
        "date_range": {"start": date(2026, 4, 1), "end": date(2026, 4, 12)},
        "has_attachment": None,
        "raw_query": None,
    }
"""

from datetime import date
from typing import Optional, TypedDict


class DateRange(TypedDict):
    """
    日付範囲（半開区間 [start, end) を推奨）

    Attributes:
        start: 開始日（None = 下限なし）
        end: 終了日（None = 上限なし）
    """

    start: Optional[date]
    end: Optional[date]


class SearchQuery(TypedDict):
    """
    Gmail検索クエリのドメイン表現

    Attributes:
        from_addr: 送信者アドレス（Gmail検索 `from:`）
        to_addr: 宛先アドレス（Gmail検索 `to:`）
        subject: 件名キーワード（Gmail検索 `subject:`）
        label: ラベル名（Gmail検索 `label:`）
        date_range: 日付範囲（`after:` / `before:` に変換）
        has_attachment: 添付ありフィルタ（`has:attachment`）
        raw_query: 生Gmailクエリ文字列（指定時は他フィールドより優先）
    """

    from_addr: Optional[str]
    to_addr: Optional[str]
    subject: Optional[str]
    label: Optional[str]
    date_range: Optional[DateRange]
    has_attachment: Optional[bool]
    raw_query: Optional[str]


__all__ = ["DateRange", "SearchQuery"]

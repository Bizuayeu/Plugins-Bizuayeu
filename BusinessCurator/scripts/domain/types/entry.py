#!/usr/bin/env python3
"""
Raw Entry Domain Type
=====================

YAML frontmatter付き md ファイルのドメイン表現。

設計意図:
- inbox/raw-entries/ に保存される単位（業務計画書 §4.1）
- ParseEmailUseCase が EmailMessage から生成
- アドレスは文字列として正規化済み（YAML serializableな形）
- datetime は date / time 文字列に分割（YAML 1.2 タイムゾーン曖昧性回避）

Usage:
    from domain.types.entry import RawEntry

    entry: RawEntry = {
        "id": "email_20260407_143022_abc123",
        "date": "2026-04-07",
        ...
    }
"""

from typing import List, Optional, TypedDict


class RawEntry(TypedDict):
    """
    生エントリ（YAML frontmatter付きmd 表現）

    inbox/raw-entries/{id}.md として保存される単位。
    triage の入力かつ absorb の素材。

    Attributes:
        id: エントリID（email_YYYYMMDD_HHMMSS_xxxx 形式、file_naming.py 参照）
        date: 送信日（YAML serializable 文字列、YYYY-MM-DD）
        time: 送信時刻（HH:MM:SS）
        source_type: ソース種別（"email"、将来 "line"/"slack" 等を想定）
        from_addr: 送信者アドレス文字列
        to_addrs: 宛先アドレス文字列リスト
        cc_addrs: CC アドレス文字列リスト
        subject: 件名
        thread_id: スレッド識別子（None 許容）
        attachments: 添付ファイル名リスト（バイナリは保持しない）
        tags: triage 後に付与されるタグ
        body: プレーンテキスト本文
    """

    id: str
    date: str
    time: str
    source_type: str
    from_addr: str
    to_addrs: List[str]
    cc_addrs: List[str]
    subject: str
    thread_id: Optional[str]
    attachments: List[str]
    tags: List[str]
    body: str


__all__ = ["RawEntry"]

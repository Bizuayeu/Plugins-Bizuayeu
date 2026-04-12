#!/usr/bin/env python3
"""
Message Domain Types
====================

Gmail API から取得した生メッセージのドメイン表現。

設計意図:
- GmailMessage は Gmail API レスポンスの最小限の情報 + 生MIME
- raw_mime は Base64URL デコード済みの bytes（そのまま .eml 書き出し可能）
- snippet はプレビュー用（Gmail API提供）
- label_ids はGmail内部ID（ラベル表示名とは別、label_map で解決する）
- BusinessCurator の EmailMessage（パース済み中間表現）とは目的が異なる

Usage:
    from datetime import datetime
    from domain.types.message import GmailMessage

    msg: GmailMessage = {
        "gmail_id": "18f3a5b1c2e4d7a9",
        "thread_id": "18f3a5b1c2e4d7a9",
        "label_ids": ["INBOX", "Label_123"],
        "snippet": "Preview text...",
        "internal_date": datetime(2026, 4, 5, 14, 30),
        "raw_mime": b"From: ...\\nTo: ...\\n\\nBody",
        "size_estimate": 4096,
    }
"""

from datetime import datetime
from typing import List, TypedDict


class GmailMessage(TypedDict):
    """
    Gmail API から取得した生メッセージ

    Attributes:
        gmail_id: Gmail API message.id（Gmail内部識別子、グローバル一意）
        thread_id: Gmail API thread.id（スレッド識別子）
        label_ids: ラベルID列（Gmail内部ID、例: "INBOX", "Label_123"）
        snippet: メッセージプレビュー（Gmail API提供、HTML除去済み）
        internal_date: Gmail API internalDate（サーバー受信日時）
        raw_mime: Base64URL デコード済みの生MIMEバイト列（.eml 書き出し用）
        size_estimate: バイト数見積もり（Gmail API提供）
    """

    gmail_id: str
    thread_id: str
    label_ids: List[str]
    snippet: str
    internal_date: datetime
    raw_mime: bytes
    size_estimate: int


__all__ = ["GmailMessage"]

#!/usr/bin/env python3
"""
Email Domain Types
==================

メールパーサー（infrastructure層）から application 層への中間表現。

設計意図:
- EmailMessage は「ファイルから読み取った生メール」のドメイン中立な表現
- RawEntry（YAML frontmatter付きmd）への変換は ParseEmailUseCase が担う
- TypedDict採用理由: dict互換、ランタイムオーバーヘッドゼロ、JSON相互運用容易

Usage:
    from domain.types.email import EmailMessage, EmailAddress, EmailAttachment

    msg: EmailMessage = {
        "message_id": "<abc@example.com>",
        "from_addr": {"name": "山田", "address": "yamada@meguru.example.jp"},
        ...
    }
"""

from datetime import datetime
from typing import List, Optional, TypedDict


class EmailAddress(TypedDict):
    """
    メールアドレス（表示名 + アドレス）

    Attributes:
        name: 表示名（無名アドレスは空文字列）
        address: メールアドレス文字列（RFC5322準拠を期待するが検証はパーサー側）

    Example:
        >>> addr: EmailAddress = {"name": "山田", "address": "yamada@meguru.example.jp"}
    """

    name: str
    address: str


class EmailAttachment(TypedDict):
    """
    メール添付ファイルのメタデータ

    Note:
        添付バイナリ本体は保持しない。filename はファイル名サニタイズ後の値を期待。

    Attributes:
        filename: 添付ファイル名
        content_type: MIME type（例: "application/pdf"）
        size: バイト数
    """

    filename: str
    content_type: str
    size: int


class EmailMessage(TypedDict):
    """
    パース済みメールメッセージ

    infrastructure/email_parser から application 層に渡される中間表現。

    Attributes:
        message_id: RFC5322 Message-ID
        from_addr: 送信者（単一）
        to_addrs: 宛先リスト
        cc_addrs: CC リスト
        subject: 件名
        date: 送信日時
        body_text: プレーンテキスト本文
        body_html: HTML 本文（None 許容）
        attachments: 添付ファイルメタデータ
        thread_id: スレッド識別子（パーサーが推定、None 許容）
        in_reply_to: RFC5322 In-Reply-To（None 許容）
        references: RFC5322 References（空 list 許容）
    """

    message_id: str
    from_addr: EmailAddress
    to_addrs: List[EmailAddress]
    cc_addrs: List[EmailAddress]
    subject: str
    date: datetime
    body_text: str
    body_html: Optional[str]
    attachments: List[EmailAttachment]
    thread_id: Optional[str]
    in_reply_to: Optional[str]
    references: List[str]


__all__ = ["EmailAddress", "EmailAttachment", "EmailMessage"]

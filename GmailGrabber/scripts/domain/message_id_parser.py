#!/usr/bin/env python3
"""
Message-ID Parser (Pure Functions)
===================================

RFC5322 Message-ID ヘッダの抽出と正規化。

設計意図:
- 純関数（副作用なし、外部依存は Python 標準 email のみ）
- Multi-user Gmail backup での重複排除キーに使う
- パース失敗は例外ではなく None で返す（防御的プログラミング）
- 正規化は RFC 5321 準拠 (ローカル部 case-sensitive, ドメイン case-insensitive)
"""

import re
from email import message_from_bytes
from email.message import Message
from email.policy import compat32
from typing import Final, Optional

_MESSAGE_ID_BODY: Final[re.Pattern[str]] = re.compile(r"<[^<>\s]+@[^<>\s]+>")


def extract_message_id(raw_mime: bytes) -> Optional[str]:
    """
    RFC5322 MIME bytes から Message-ID ヘッダ値を抽出する。

    Args:
        raw_mime: Base64URL デコード済みの生 MIME バイト列 (GmailMessage.raw_mime)

    Returns:
        Message-ID ヘッダ値 (山括弧含む、例: "<abc123@example.com>")。
        ヘッダ無し / パース失敗 / 空入力 → None

    Notes:
        - Python 標準 email パーサ使用（ヘッダ大文字小文字を吸収）
        - 複数行ヘッダ (unfolded) は email パーサが自動処理
        - パース例外は全て吸収して None を返す
    """
    if not raw_mime:
        return None
    try:
        msg: Message = message_from_bytes(raw_mime, policy=compat32)
    except Exception:  # noqa: BLE001
        return None

    value = msg.get("Message-ID") or msg.get("Message-Id") or msg.get("message-id")
    if value is None:
        return None

    stripped = value.strip()
    if not stripped:
        return None

    match = _MESSAGE_ID_BODY.search(stripped)
    return match.group(0) if match else stripped


def normalize_message_id(message_id: str, *, strip_brackets: bool = False) -> str:
    """
    Message-ID を比較用に正規化する。

    RFC 5321 準拠: ローカル部は case-sensitive、ドメイン部のみ case-insensitive。

    Args:
        message_id: "<local@Domain.COM>" 形式または生の "<x>" 文字列
        strip_brackets: True なら最終結果から山括弧を除去

    Returns:
        正規化済み Message-ID
    """
    s = message_id.strip()
    if s.startswith("<") and s.endswith(">"):
        inner = s[1:-1]
    else:
        inner = s

    if "@" in inner:
        local, _, domain = inner.partition("@")
        normalized_inner = f"{local}@{domain.lower()}"
    else:
        normalized_inner = inner

    if strip_brackets:
        return normalized_inner
    return f"<{normalized_inner}>"


__all__ = ["extract_message_id", "normalize_message_id"]

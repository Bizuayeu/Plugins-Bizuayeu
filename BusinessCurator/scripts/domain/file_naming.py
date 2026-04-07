#!/usr/bin/env python3
"""
File Naming Utilities
=====================

エントリID生成とファイル名サニタイズの純粋関数群。

設計意図:
- make_entry_id: datetime + メッセージID hash → "email_YYYYMMDD_HHMMSS_xxxxxxxx"
- parse_entry_id: 逆操作（ラウンドトリップ可能）
- sanitize_filename: Windows/Linux 共通で安全なファイル名生成
- 全関数は冪等（同じ入力なら同じ出力）
- 外部依存なし（hashlib のみ標準ライブラリ）

Usage:
    from datetime import datetime
    from domain.file_naming import make_entry_id

    eid = make_entry_id(datetime(2026, 4, 7, 14, 30, 22), "<abc@example.com>")
    # → "email_20260407_143022_a1b2c3d4"
"""

import hashlib
import re
from datetime import datetime
from typing import Tuple

from domain.constants import ENTRY_ID_HASH_LENGTH, ENTRY_ID_PREFIX

__all__ = [
    "is_valid_entry_id",
    "make_entry_id",
    "parse_entry_id",
    "sanitize_filename",
]


# =============================================================================
# Entry ID
# =============================================================================

# email_YYYYMMDD_HHMMSS_xxxxxxxx 形式
_ENTRY_ID_PATTERN = re.compile(
    r"^"
    + re.escape(ENTRY_ID_PREFIX)
    + r"(?P<date>\d{8})_(?P<time>\d{6})_(?P<hash>[0-9a-f]{"
    + str(ENTRY_ID_HASH_LENGTH)
    + r"})$"
)


def make_entry_id(dt: datetime, message_id: str) -> str:
    """
    エントリID を生成

    Args:
        dt: メール送信日時
        message_id: RFC5322 Message-ID（衝突回避用、空文字列許容）

    Returns:
        "email_YYYYMMDD_HHMMSS_xxxxxxxx" 形式の文字列

    Note:
        同じ (dt, message_id) ペアは常に同じ ID を返す（冪等性）。
        message_id は SHA-256 → 先頭 ENTRY_ID_HASH_LENGTH 文字で切り詰め。
    """
    date_part = dt.strftime("%Y%m%d")
    time_part = dt.strftime("%H%M%S")
    hash_full = hashlib.sha256(message_id.encode("utf-8")).hexdigest()
    hash_part = hash_full[:ENTRY_ID_HASH_LENGTH]
    return f"{ENTRY_ID_PREFIX}{date_part}_{time_part}_{hash_part}"


def parse_entry_id(entry_id: str) -> Tuple[datetime, str]:
    """
    エントリID を datetime と hash サフィックスに分解

    Args:
        entry_id: make_entry_id が生成した形式の文字列

    Returns:
        (datetime, hash_suffix) のタプル

    Raises:
        ValueError: フォーマット不正、または日付パース不能
    """
    m = _ENTRY_ID_PATTERN.match(entry_id)
    if not m:
        raise ValueError(f"invalid entry_id format: {entry_id!r}")
    date_str = m.group("date")
    time_str = m.group("time")
    hash_str = m.group("hash")
    try:
        dt = datetime.strptime(f"{date_str}{time_str}", "%Y%m%d%H%M%S")
    except ValueError as e:
        raise ValueError(f"invalid date in entry_id: {entry_id!r}") from e
    return dt, hash_str


def is_valid_entry_id(entry_id: str) -> bool:
    """
    エントリID として有効かを判定

    Args:
        entry_id: 検査対象文字列

    Returns:
        有効なら True、それ以外は False（例外を投げない）
    """
    try:
        parse_entry_id(entry_id)
    except ValueError:
        return False
    return True


# =============================================================================
# Filename Sanitization
# =============================================================================

# Windows で禁止される文字
_FORBIDDEN_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')

# 最大長（NTFS / ext4 共通の安全側）
_MAX_FILENAME_LENGTH = 255


def sanitize_filename(name: str) -> str:
    """
    OS 共通で安全なファイル名に変換

    Args:
        name: 元のファイル名（パス区切りを含む可能性がある）

    Returns:
        サニタイズ済みのファイル名

    Raises:
        ValueError: 空文字列、空白のみ、"." または ".." の場合

    Note:
        - Windows 禁止文字（< > : " / \\ | ? * 制御文字）を _ に置換
        - 前後空白を除去
        - 255 文字超は切り詰め（拡張子は保持）
        - 日本語は保持される
    """
    stripped = name.strip()
    if not stripped:
        raise ValueError("filename cannot be empty or whitespace only")
    if stripped in (".", ".."):
        raise ValueError(f"filename cannot be {stripped!r}")

    # 禁止文字を _ に置換
    sanitized = _FORBIDDEN_CHARS.sub("_", stripped)

    # 長さチェック（拡張子保持）
    if len(sanitized) > _MAX_FILENAME_LENGTH:
        # 拡張子を取り出して残りを切り詰め
        if "." in sanitized:
            stem, ext = sanitized.rsplit(".", 1)
            ext_with_dot = "." + ext
            allowed_stem_len = _MAX_FILENAME_LENGTH - len(ext_with_dot)
            sanitized = stem[:allowed_stem_len] + ext_with_dot
        else:
            sanitized = sanitized[:_MAX_FILENAME_LENGTH]

    return sanitized

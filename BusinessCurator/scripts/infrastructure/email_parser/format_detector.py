#!/usr/bin/env python3
"""
EmailFormat Detector
====================

メールファイルのフォーマット (.eml / .mbox) 自動判定。

判定戦略:
1. 拡張子優先（.eml, .mbox の大文字小文字は区別しない）
2. 拡張子曖昧（.txt 等）の場合はファイル先頭のシグネチャ
3. mbox: "From " で始まる行（mbox separator）
4. eml: "<Field>: " 形式のヘッダ行
"""

import re
from enum import Enum
from pathlib import Path

__all__ = ["EmailFormat", "detect_email_format"]


class EmailFormat(Enum):
    """検出されたメールフォーマット"""

    EML = "eml"
    MBOX = "mbox"


# mbox separator: "From <addr> <date>"
_MBOX_SEPARATOR_RE = re.compile(r"^From .+\d{4}\s*$")
# RFC5322 ヘッダ: "Field-Name: value"
_HEADER_RE = re.compile(r"^[A-Za-z][A-Za-z0-9-]*:\s")


def detect_email_format(path: Path) -> EmailFormat:
    """
    ファイルのフォーマットを判定

    Args:
        path: 検査対象パス

    Returns:
        EmailFormat

    Raises:
        FileNotFoundError: ファイル不存在
        IsADirectoryError: ディレクトリ指定
        ValueError: 判定不能
    """
    if not path.exists():
        raise FileNotFoundError(f"file not found: {path}")
    if path.is_dir():
        raise IsADirectoryError(f"expected file, got directory: {path}")

    # 拡張子優先
    suffix = path.suffix.lower()
    if suffix == ".eml":
        return EmailFormat.EML
    if suffix == ".mbox":
        return EmailFormat.MBOX

    # シグネチャ判定
    with path.open("r", encoding="utf-8", errors="replace") as f:
        first_line = f.readline()

    if _MBOX_SEPARATOR_RE.match(first_line):
        return EmailFormat.MBOX
    if _HEADER_RE.match(first_line):
        return EmailFormat.EML

    raise ValueError(f"cannot detect email format: {path}")

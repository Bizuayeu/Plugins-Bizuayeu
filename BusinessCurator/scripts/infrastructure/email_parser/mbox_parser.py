#!/usr/bin/env python3
"""
MboxEmailParser
===============

EmailParserProtocol の .mbox 実装。

設計意図:
- Python 標準 `mailbox.mbox` を利用
- 各メッセージは EmlEmailParser._convert で EmailMessage に変換
- 順序保持（mbox の物理順）
"""

import email
import mailbox
from email.policy import default as default_policy
from pathlib import Path
from typing import List

from domain.exceptions import IngestError
from domain.types.email import EmailMessage
from infrastructure.email_parser.eml_parser import EmlEmailParser

__all__ = ["MboxEmailParser"]


class MboxEmailParser:
    """`.mbox` ファイルパーサー"""

    def parse(self, path: Path) -> EmailMessage:
        """
        .mbox 内の最初のメッセージを返す

        Args:
            path: .mbox ファイルパス

        Returns:
            EmailMessage（先頭1通）

        Raises:
            IngestError: ファイル不存在、または空 mbox
        """
        messages = self.parse_many(path)
        if not messages:
            raise IngestError(f"empty mbox: {path}")
        return messages[0]

    def parse_many(self, path: Path) -> List[EmailMessage]:
        """
        .mbox 全メッセージをパース

        Args:
            path: .mbox ファイルパス

        Returns:
            EmailMessage のリスト（物理順）

        Raises:
            IngestError: 読み込み失敗
        """
        if not path.exists():
            raise IngestError(f"file not found: {path}")

        try:
            mbox = mailbox.mbox(str(path))
        except Exception as e:
            raise IngestError(f"failed to open mbox {path}: {e}") from e

        try:
            results: List[EmailMessage] = []
            for msg in mbox:
                # mailbox は古い API の Message を返すため、bytes 経由で
                # policy.default の EmailMessage に再パースする
                raw_bytes = bytes(msg)
                modern_msg = email.message_from_bytes(raw_bytes, policy=default_policy)
                results.append(EmlEmailParser._convert(modern_msg))
            return results
        except Exception as e:
            raise IngestError(f"failed to parse mbox {path}: {e}") from e
        finally:
            mbox.close()

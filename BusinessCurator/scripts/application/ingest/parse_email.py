#!/usr/bin/env python3
"""
ParseEmailUseCase
=================

EmailMessage（パーサー出力）→ RawEntry（YAML frontmatter付き md 用）変換。

設計意図:
- 純粋変換ロジック（I/O なし、外部依存なし）
- ParseEmailUseCase は「中間表現の正規化」を担う
- thread_id は明示提供 > in_reply_to > references[0] > None の順で決定
- 添付ファイルは filename のみ抽出（バイナリ非保持）
- 生成された RawEntry は domain.validation.validate_raw_entry を満たす
"""

from domain.file_naming import make_entry_id
from domain.types.email import EmailMessage
from domain.types.entry import RawEntry

__all__ = ["ParseEmailUseCase"]


class ParseEmailUseCase:
    """EmailMessage を RawEntry に変換するユースケース"""

    def execute(self, message: EmailMessage) -> RawEntry:
        """
        EmailMessage を RawEntry に変換

        Args:
            message: パーサーから受け取った中間表現

        Returns:
            RawEntry（YAML frontmatter として md ファイルに書ける形）
        """
        dt = message["date"]
        entry_id = make_entry_id(dt, message["message_id"])

        thread_id = self._resolve_thread_id(message)

        return {
            "id": entry_id,
            "date": dt.strftime("%Y-%m-%d"),
            "time": dt.strftime("%H:%M:%S"),
            "source_type": "email",
            "from_addr": message["from_addr"]["address"],
            "to_addrs": [a["address"] for a in message["to_addrs"]],
            "cc_addrs": [a["address"] for a in message["cc_addrs"]],
            "subject": message["subject"],
            "thread_id": thread_id,
            "attachments": [a["filename"] for a in message["attachments"]],
            "tags": [],
            "body": message["body_text"],
        }

    @staticmethod
    def _resolve_thread_id(message: EmailMessage) -> str | None:
        """thread_id 決定ルール: 明示 > in_reply_to > references[0] > None"""
        if message["thread_id"]:
            return message["thread_id"]
        if message["in_reply_to"]:
            return message["in_reply_to"]
        if message["references"]:
            return message["references"][0]
        return None

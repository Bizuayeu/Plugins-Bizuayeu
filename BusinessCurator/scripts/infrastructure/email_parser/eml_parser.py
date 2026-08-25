#!/usr/bin/env python3
"""
EmlEmailParser
==============

EmailParserProtocol の .eml 実装。

設計意図:
- Python 標準 `email` モジュール (email.parser, email.policy.default) を利用
- multipart 対応: text/plain 部分を本文として抽出、添付は filename のみ
- ヘッダの MIME encoded-word を自動デコード（policy.default の挙動）
- 不正ファイルや読み込み失敗は IngestError でラップ
"""

import email
from datetime import datetime, timezone
from email.message import Message
from email.policy import default as default_policy
from email.utils import getaddresses, parseaddr, parsedate_to_datetime
from pathlib import Path

from domain.exceptions import IngestError
from domain.types.email import EmailAddress, EmailAttachment, EmailMessage

__all__ = ["EmlEmailParser"]


class EmlEmailParser:
    """`.eml` ファイルパーサー（標準 email モジュールベース）"""

    def parse(self, path: Path) -> EmailMessage:
        """
        単一 .eml をパース

        Args:
            path: .eml ファイルパス

        Returns:
            EmailMessage

        Raises:
            IngestError: 読み込み・パース失敗
        """
        try:
            with path.open("rb") as f:
                msg = email.message_from_binary_file(f, policy=default_policy)
        except FileNotFoundError as e:
            raise IngestError(f"file not found: {path}") from e
        except OSError as e:
            raise IngestError(f"failed to read {path}: {e}") from e

        return self._convert(msg)

    def parse_many(self, path: Path) -> list[EmailMessage]:
        """
        単体 .eml は要素1のリストとして返す

        Args:
            path: .eml ファイルパス

        Returns:
            EmailMessage のリスト
        """
        return [self.parse(path)]

    # ------------------------------------------------------------------
    # internal
    # ------------------------------------------------------------------

    @classmethod
    def _convert(cls, msg: Message) -> EmailMessage:
        """email.message.Message → EmailMessage TypedDict"""
        message_id = (msg.get("Message-ID") or "").strip()
        from_addr = cls._parse_single_address(msg.get("From"))
        to_addrs = cls._parse_address_list(msg.get_all("To"))
        cc_addrs = cls._parse_address_list(msg.get_all("Cc"))
        subject = (msg.get("Subject") or "").strip()
        date = cls._parse_date(msg.get("Date"))

        body_text, body_html = cls._extract_bodies(msg)
        attachments = cls._extract_attachments(msg)

        in_reply_to: str | None = msg.get("In-Reply-To")
        if in_reply_to is not None:
            in_reply_to = in_reply_to.strip()
        references_raw = msg.get("References") or ""
        references = [r.strip() for r in references_raw.split() if r.strip()]

        return {
            "message_id": message_id,
            "from_addr": from_addr,
            "to_addrs": to_addrs,
            "cc_addrs": cc_addrs,
            "subject": subject,
            "date": date,
            "body_text": body_text,
            "body_html": body_html,
            "attachments": attachments,
            "thread_id": None,
            "in_reply_to": in_reply_to,
            "references": references,
        }

    # ------------------------------------------------------------------
    # ヘルパ
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_single_address(raw: str | None) -> EmailAddress:
        if not raw:
            return {"name": "", "address": ""}
        name, addr = parseaddr(raw)
        return {"name": name or "", "address": addr or ""}

    @staticmethod
    def _parse_address_list(values: list[str] | None) -> list[EmailAddress]:
        if not values:
            return []
        results: list[EmailAddress] = []
        for name, addr in getaddresses(values):
            if not addr:
                continue
            results.append({"name": name or "", "address": addr})
        return results

    @staticmethod
    def _parse_date(raw: str | None) -> datetime:
        if not raw:
            # 不在時はエポックを返す（呼び出し側でハンドリング可能）
            return datetime.fromtimestamp(0, tz=timezone.utc)
        try:
            dt = parsedate_to_datetime(raw)
        except (TypeError, ValueError) as e:
            raise IngestError(f"invalid Date header: {raw!r}") from e
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt

    @classmethod
    def _extract_bodies(cls, msg: Message) -> tuple[str, str | None]:
        """text/plain 本文と text/html 本文を取得"""
        text_part: str | None = None
        html_part: str | None = None

        if msg.is_multipart():
            for part in msg.walk():
                ctype = part.get_content_type()
                disposition = (part.get("Content-Disposition") or "").lower()
                if "attachment" in disposition:
                    continue
                if ctype == "text/plain" and text_part is None:
                    text_part = cls._get_part_text(part)
                elif ctype == "text/html" and html_part is None:
                    html_part = cls._get_part_text(part)
        else:
            ctype = msg.get_content_type()
            content = cls._get_part_text(msg)
            if ctype == "text/plain":
                text_part = content
            elif ctype == "text/html":
                html_part = content
            else:
                text_part = content

        return text_part or "", html_part

    @staticmethod
    def _get_part_text(part: Message) -> str:
        """multipart の1パートからテキストを取り出す（payload + charset 経由）"""
        payload = part.get_payload(decode=True)
        if not isinstance(payload, bytes):
            return ""
        charset = part.get_content_charset() or "utf-8"
        try:
            return payload.decode(charset, errors="replace")
        except LookupError:
            # 未知の charset → utf-8 にフォールバック
            return payload.decode("utf-8", errors="replace")

    @staticmethod
    def _extract_attachments(msg: Message) -> list[EmailAttachment]:
        results: list[EmailAttachment] = []
        if not msg.is_multipart():
            return results
        for part in msg.walk():
            disposition = (part.get("Content-Disposition") or "").lower()
            if "attachment" not in disposition:
                continue
            filename = part.get_filename() or "unnamed"
            ctype = part.get_content_type()
            payload = part.get_payload(decode=True)
            size = len(payload) if isinstance(payload, bytes) else 0
            results.append(
                {
                    "filename": filename,
                    "content_type": ctype,
                    "size": size,
                }
            )
        return results

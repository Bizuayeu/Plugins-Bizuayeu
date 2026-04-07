#!/usr/bin/env python3
"""
domain/types/email.py テスト
============================

EmailMessage / EmailAddress / EmailAttachment TypedDictのフィールド検証。

設計意図:
- EmailMessage はメールパーサーの中間表現（infrastructure → application境界）
- RawEntry（YAML frontmatter付きmd）とは別物。RawEntryへの変換は ParseEmailUseCase が担う
- TypedDict は実行時型ではないため、検証は get_type_hints で行う
"""

from datetime import datetime
from typing import List, Optional, get_type_hints

import pytest

from domain.types.email import EmailAddress, EmailAttachment, EmailMessage

# =============================================================================
# EmailAddress
# =============================================================================


class TestEmailAddress:
    """EmailAddress TypedDict のテスト"""

    @pytest.mark.unit
    def test_has_name_field(self) -> None:
        """name フィールド（表示名、空文字列許容）"""
        hints = get_type_hints(EmailAddress)
        assert "name" in hints
        assert hints["name"] is str

    @pytest.mark.unit
    def test_has_address_field(self) -> None:
        """address フィールド（メールアドレス文字列）"""
        hints = get_type_hints(EmailAddress)
        assert "address" in hints
        assert hints["address"] is str

    @pytest.mark.unit
    def test_can_construct_with_name_and_address(self) -> None:
        """name と address だけで構築可能"""
        addr: EmailAddress = {"name": "市川", "address": "ichikawa@meguru.co.jp"}
        assert addr["name"] == "市川"
        assert addr["address"] == "ichikawa@meguru.co.jp"

    @pytest.mark.unit
    def test_empty_name_is_allowed(self) -> None:
        """name は空文字列でも良い（無名アドレス対応）"""
        addr: EmailAddress = {"name": "", "address": "noreply@example.com"}
        assert addr["name"] == ""


# =============================================================================
# EmailAttachment
# =============================================================================


class TestEmailAttachment:
    """EmailAttachment TypedDict のテスト"""

    @pytest.mark.unit
    def test_has_filename_field(self) -> None:
        """filename フィールド"""
        hints = get_type_hints(EmailAttachment)
        assert "filename" in hints
        assert hints["filename"] is str

    @pytest.mark.unit
    def test_has_content_type_field(self) -> None:
        """content_type フィールド（MIME type）"""
        hints = get_type_hints(EmailAttachment)
        assert "content_type" in hints
        assert hints["content_type"] is str

    @pytest.mark.unit
    def test_has_size_field(self) -> None:
        """size フィールド（バイト数）"""
        hints = get_type_hints(EmailAttachment)
        assert "size" in hints
        assert hints["size"] is int

    @pytest.mark.unit
    def test_can_construct(self) -> None:
        """filename / content_type / size で構築可能"""
        att: EmailAttachment = {
            "filename": "排煙計算書.pdf",
            "content_type": "application/pdf",
            "size": 102400,
        }
        assert att["filename"] == "排煙計算書.pdf"
        assert att["size"] == 102400


# =============================================================================
# EmailMessage
# =============================================================================


class TestEmailMessage:
    """EmailMessage TypedDict のテスト"""

    @pytest.mark.unit
    def test_has_message_id_field(self) -> None:
        """message_id フィールド（RFC5322 Message-ID）"""
        hints = get_type_hints(EmailMessage)
        assert "message_id" in hints
        assert hints["message_id"] is str

    @pytest.mark.unit
    def test_has_from_addr_field(self) -> None:
        """from_addr フィールド（送信者は単一）"""
        hints = get_type_hints(EmailMessage)
        assert "from_addr" in hints
        assert hints["from_addr"] is EmailAddress

    @pytest.mark.unit
    def test_has_to_addrs_field(self) -> None:
        """to_addrs フィールド（複数宛先）"""
        hints = get_type_hints(EmailMessage)
        assert "to_addrs" in hints
        assert hints["to_addrs"] == List[EmailAddress]

    @pytest.mark.unit
    def test_has_cc_addrs_field(self) -> None:
        """cc_addrs フィールド（複数CC）"""
        hints = get_type_hints(EmailMessage)
        assert "cc_addrs" in hints
        assert hints["cc_addrs"] == List[EmailAddress]

    @pytest.mark.unit
    def test_has_subject_field(self) -> None:
        """subject フィールド"""
        hints = get_type_hints(EmailMessage)
        assert "subject" in hints
        assert hints["subject"] is str

    @pytest.mark.unit
    def test_has_date_field(self) -> None:
        """date フィールド（datetime オブジェクト、タイムゾーン情報含む想定）"""
        hints = get_type_hints(EmailMessage)
        assert "date" in hints
        assert hints["date"] is datetime

    @pytest.mark.unit
    def test_has_body_text_field(self) -> None:
        """body_text フィールド（プレーンテキスト本文）"""
        hints = get_type_hints(EmailMessage)
        assert "body_text" in hints
        assert hints["body_text"] is str

    @pytest.mark.unit
    def test_has_body_html_field(self) -> None:
        """body_html フィールド（HTML本文、None許容）"""
        hints = get_type_hints(EmailMessage)
        assert "body_html" in hints
        assert hints["body_html"] == Optional[str]

    @pytest.mark.unit
    def test_has_attachments_field(self) -> None:
        """attachments フィールド"""
        hints = get_type_hints(EmailMessage)
        assert "attachments" in hints
        assert hints["attachments"] == List[EmailAttachment]

    @pytest.mark.unit
    def test_has_thread_id_field(self) -> None:
        """thread_id フィールド（None許容、後段でスレッド推定）"""
        hints = get_type_hints(EmailMessage)
        assert "thread_id" in hints
        assert hints["thread_id"] == Optional[str]

    @pytest.mark.unit
    def test_has_in_reply_to_field(self) -> None:
        """in_reply_to フィールド（RFC5322 In-Reply-To、None許容）"""
        hints = get_type_hints(EmailMessage)
        assert "in_reply_to" in hints
        assert hints["in_reply_to"] == Optional[str]

    @pytest.mark.unit
    def test_has_references_field(self) -> None:
        """references フィールド（RFC5322 References、空list許容）"""
        hints = get_type_hints(EmailMessage)
        assert "references" in hints
        assert hints["references"] == List[str]

    @pytest.mark.unit
    def test_can_construct_minimal(self) -> None:
        """最小構成で構築可能"""
        msg: EmailMessage = {
            "message_id": "<abc123@meguru.co.jp>",
            "from_addr": {"name": "市川", "address": "ichikawa@meguru.co.jp"},
            "to_addrs": [{"name": "大環主", "address": "oowanushi@meguru.co.jp"}],
            "cc_addrs": [],
            "subject": "○○マンション排煙設備",
            "date": datetime(2026, 4, 7, 14, 30, 22),
            "body_text": "市川です。",
            "body_html": None,
            "attachments": [],
            "thread_id": None,
            "in_reply_to": None,
            "references": [],
        }
        assert msg["message_id"] == "<abc123@meguru.co.jp>"
        assert msg["from_addr"]["address"] == "ichikawa@meguru.co.jp"
        assert len(msg["to_addrs"]) == 1
        assert msg["body_html"] is None

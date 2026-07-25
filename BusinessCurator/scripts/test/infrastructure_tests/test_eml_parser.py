#!/usr/bin/env python3
"""
infrastructure/email_parser/eml_parser.py テスト
==================================================

EmlEmailParser の .eml パース動作検証。

検証ポイント:
- 単純な .eml: from/to/subject/date/body
- マルチパート: text/plain 本文 + 添付ファイル名抽出
- 日本語ヘッダ（MIME encoded-word）デコード
- in_reply_to / references パース
- 不存在ファイルで IngestError
"""

from datetime import datetime
from pathlib import Path

import pytest

from infrastructure.email_parser.eml_parser import EmlEmailParser

# =============================================================================
# Fixtures
# =============================================================================

FIXTURE_DIR = Path(__file__).parent.parent / "fixtures" / "emails"


# =============================================================================
# 単純メール
# =============================================================================


class TestEmlEmailParserSimple:
    @pytest.fixture
    def parser(self) -> EmlEmailParser:
        return EmlEmailParser()

    @pytest.mark.integration
    def test_parse_message_id(self, parser: EmlEmailParser) -> None:
        result = parser.parse(FIXTURE_DIR / "sample_simple.eml")
        assert result["message_id"] == "<abc123@example.com>"

    @pytest.mark.integration
    def test_parse_from(self, parser: EmlEmailParser) -> None:
        result = parser.parse(FIXTURE_DIR / "sample_simple.eml")
        assert result["from_addr"]["address"] == "sender@example.com"
        assert result["from_addr"]["name"] == "Sender Name"

    @pytest.mark.integration
    def test_parse_to(self, parser: EmlEmailParser) -> None:
        result = parser.parse(FIXTURE_DIR / "sample_simple.eml")
        assert len(result["to_addrs"]) == 1
        assert result["to_addrs"][0]["address"] == "recipient@example.com"

    @pytest.mark.integration
    def test_parse_subject(self, parser: EmlEmailParser) -> None:
        result = parser.parse(FIXTURE_DIR / "sample_simple.eml")
        assert result["subject"] == "Test Subject"

    @pytest.mark.integration
    def test_parse_date(self, parser: EmlEmailParser) -> None:
        result = parser.parse(FIXTURE_DIR / "sample_simple.eml")
        assert isinstance(result["date"], datetime)
        assert result["date"].year == 2026
        assert result["date"].month == 4
        assert result["date"].day == 7

    @pytest.mark.integration
    def test_parse_body(self, parser: EmlEmailParser) -> None:
        result = parser.parse(FIXTURE_DIR / "sample_simple.eml")
        assert "simple test email body" in result["body_text"]
        assert "Multiple lines" in result["body_text"]

    @pytest.mark.integration
    def test_no_attachments(self, parser: EmlEmailParser) -> None:
        result = parser.parse(FIXTURE_DIR / "sample_simple.eml")
        assert result["attachments"] == []


# =============================================================================
# マルチパート + 日本語
# =============================================================================


class TestEmlEmailParserMultipart:
    @pytest.fixture
    def parser(self) -> EmlEmailParser:
        return EmlEmailParser()

    @pytest.mark.integration
    def test_parse_multipart_body_text(self, parser: EmlEmailParser) -> None:
        result = parser.parse(FIXTURE_DIR / "sample_multipart.eml")
        assert "本文" in result["body_text"]

    @pytest.mark.integration
    def test_parse_multipart_attachment_filename(self, parser: EmlEmailParser) -> None:
        result = parser.parse(FIXTURE_DIR / "sample_multipart.eml")
        filenames = [a["filename"] for a in result["attachments"]]
        assert "report.pdf" in filenames

    @pytest.mark.integration
    def test_parse_cc_addresses(self, parser: EmlEmailParser) -> None:
        result = parser.parse(FIXTURE_DIR / "sample_multipart.eml")
        cc_addresses = [a["address"] for a in result["cc_addrs"]]
        assert "honma@meguru.example.jp" in cc_addresses
        assert "mori@meguru.example.jp" in cc_addresses


# =============================================================================
# スレッド情報
# =============================================================================


class TestEmlEmailParserThread:
    @pytest.fixture
    def parser(self) -> EmlEmailParser:
        return EmlEmailParser()

    @pytest.mark.integration
    def test_parse_in_reply_to(self, parser: EmlEmailParser) -> None:
        result = parser.parse(FIXTURE_DIR / "sample_thread_reply.eml")
        assert result["in_reply_to"] == "<original-msg@example.com>"

    @pytest.mark.integration
    def test_parse_references(self, parser: EmlEmailParser) -> None:
        result = parser.parse(FIXTURE_DIR / "sample_thread_reply.eml")
        assert "<original-msg@example.com>" in result["references"]
        assert "<middle-msg@example.com>" in result["references"]


# =============================================================================
# parse_many
# =============================================================================


class TestEmlEmailParserParseMany:
    @pytest.fixture
    def parser(self) -> EmlEmailParser:
        return EmlEmailParser()

    @pytest.mark.integration
    def test_parse_many_single_eml(self, parser: EmlEmailParser) -> None:
        """単体 .eml に対しては 1 要素のリスト"""
        result = parser.parse_many(FIXTURE_DIR / "sample_simple.eml")
        assert len(result) == 1
        assert result[0]["message_id"] == "<abc123@example.com>"


# =============================================================================
# エラー
# =============================================================================


class TestEmlEmailParserErrors:
    @pytest.fixture
    def parser(self) -> EmlEmailParser:
        return EmlEmailParser()

    @pytest.mark.integration
    def test_nonexistent_file_raises(self, parser: EmlEmailParser, tmp_path) -> None:  # type: ignore[no-untyped-def]
        from domain.exceptions import IngestError

        with pytest.raises(IngestError):
            parser.parse(tmp_path / "nonexistent.eml")

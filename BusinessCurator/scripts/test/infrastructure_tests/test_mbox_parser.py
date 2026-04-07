#!/usr/bin/env python3
"""
infrastructure/email_parser/mbox_parser.py テスト
==================================================

MboxEmailParser の .mbox パース動作検証。
"""

from pathlib import Path

import pytest

from infrastructure.email_parser.mbox_parser import MboxEmailParser

FIXTURE_DIR = Path(__file__).parent.parent / "fixtures" / "emails"


class TestMboxEmailParser:
    @pytest.fixture
    def parser(self) -> MboxEmailParser:
        return MboxEmailParser()

    @pytest.mark.integration
    def test_parse_many_returns_5_messages(self, parser: MboxEmailParser) -> None:
        result = parser.parse_many(FIXTURE_DIR / "sample_5_messages.mbox")
        assert len(result) == 5

    @pytest.mark.integration
    def test_parse_many_message_ids_in_order(self, parser: MboxEmailParser) -> None:
        result = parser.parse_many(FIXTURE_DIR / "sample_5_messages.mbox")
        ids = [m["message_id"] for m in result]
        assert ids == [
            "<msg001@example.com>",
            "<msg002@example.com>",
            "<msg003@example.com>",
            "<msg004@example.com>",
            "<msg005@example.com>",
        ]

    @pytest.mark.integration
    def test_parse_many_subjects(self, parser: MboxEmailParser) -> None:
        result = parser.parse_many(FIXTURE_DIR / "sample_5_messages.mbox")
        subjects = [m["subject"] for m in result]
        assert "First message" in subjects
        assert "Fifth message" in subjects

    @pytest.mark.integration
    def test_parse_many_extracts_bodies(self, parser: MboxEmailParser) -> None:
        result = parser.parse_many(FIXTURE_DIR / "sample_5_messages.mbox")
        bodies = [m["body_text"] for m in result]
        assert any("first message" in b for b in bodies)

    @pytest.mark.integration
    def test_parse_single_calls_parse_many_first(self, parser: MboxEmailParser) -> None:
        """parse は parse_many の最初を返す"""
        result = parser.parse(FIXTURE_DIR / "sample_5_messages.mbox")
        assert result["message_id"] == "<msg001@example.com>"

    @pytest.mark.integration
    def test_nonexistent_file_raises(self, parser: MboxEmailParser, tmp_path) -> None:  # type: ignore[no-untyped-def]
        from domain.exceptions import IngestError

        with pytest.raises(IngestError):
            parser.parse_many(tmp_path / "nope.mbox")

    @pytest.mark.integration
    def test_empty_mbox_file(self, parser: MboxEmailParser, tmp_path) -> None:  # type: ignore[no-untyped-def]
        empty = tmp_path / "empty.mbox"
        empty.write_text("")
        result = parser.parse_many(empty)
        assert result == []

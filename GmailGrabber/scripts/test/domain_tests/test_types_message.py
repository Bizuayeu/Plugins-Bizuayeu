#!/usr/bin/env python3
"""
domain/types/message.py テスト
==============================

GmailMessage TypedDict のフィールド検証。
"""

from datetime import datetime
from typing import get_type_hints

import pytest

from domain.types.message import GmailMessage


class TestGmailMessage:
    """GmailMessage TypedDict のテスト"""

    @pytest.mark.unit
    def test_has_gmail_id_field(self) -> None:
        hints = get_type_hints(GmailMessage)
        assert "gmail_id" in hints
        assert hints["gmail_id"] is str

    @pytest.mark.unit
    def test_has_thread_id_field(self) -> None:
        hints = get_type_hints(GmailMessage)
        assert "thread_id" in hints
        assert hints["thread_id"] is str

    @pytest.mark.unit
    def test_has_label_ids_field(self) -> None:
        hints = get_type_hints(GmailMessage)
        assert "label_ids" in hints

    @pytest.mark.unit
    def test_has_snippet_field(self) -> None:
        hints = get_type_hints(GmailMessage)
        assert "snippet" in hints
        assert hints["snippet"] is str

    @pytest.mark.unit
    def test_has_internal_date_field(self) -> None:
        hints = get_type_hints(GmailMessage)
        assert "internal_date" in hints

    @pytest.mark.unit
    def test_has_raw_mime_field(self) -> None:
        hints = get_type_hints(GmailMessage)
        assert "raw_mime" in hints
        assert hints["raw_mime"] is bytes

    @pytest.mark.unit
    def test_has_size_estimate_field(self) -> None:
        hints = get_type_hints(GmailMessage)
        assert "size_estimate" in hints
        assert hints["size_estimate"] is int

    @pytest.mark.unit
    def test_can_construct_minimal_message(self) -> None:
        msg: GmailMessage = {
            "gmail_id": "18f3a5b1c2e4d7a9",
            "thread_id": "18f3a5b1c2e4d7a9",
            "label_ids": ["INBOX"],
            "snippet": "Preview",
            "internal_date": datetime(2026, 4, 5, 14, 30),
            "raw_mime": b"From: test@example.com\n\nBody",
            "size_estimate": 1024,
        }
        assert msg["gmail_id"] == "18f3a5b1c2e4d7a9"
        assert isinstance(msg["raw_mime"], bytes)
        assert msg["size_estimate"] == 1024

    @pytest.mark.unit
    def test_raw_mime_is_bytes_for_eml_writability(self) -> None:
        """raw_mime は .eml ファイルにそのまま書き出せるバイト列"""
        msg: GmailMessage = {
            "gmail_id": "x",
            "thread_id": "x",
            "label_ids": [],
            "snippet": "",
            "internal_date": datetime(2026, 4, 1),
            "raw_mime": b"MIME-Version: 1.0\r\n\r\nbody",
            "size_estimate": 30,
        }
        assert msg["raw_mime"].startswith(b"MIME-Version")

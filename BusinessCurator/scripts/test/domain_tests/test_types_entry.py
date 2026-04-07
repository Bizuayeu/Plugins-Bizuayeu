#!/usr/bin/env python3
"""
domain/types/entry.py テスト
============================

RawEntry TypedDictのフィールド検証。

設計意図:
- RawEntry は YAML frontmatter付き md ファイルのドメイン表現
- inbox/raw-entries/ に保存される単位
- ParseEmailUseCase が EmailMessage から生成する
"""

from typing import List, Optional, get_type_hints

import pytest

from domain.types.entry import RawEntry

# =============================================================================
# RawEntry
# =============================================================================


class TestRawEntry:
    """RawEntry TypedDict のテスト（業務計画書 §4.1 準拠）"""

    @pytest.mark.unit
    def test_has_id_field(self) -> None:
        """id フィールド（email_YYYYMMDD_HHMMSS_xxxx 形式）"""
        hints = get_type_hints(RawEntry)
        assert "id" in hints
        assert hints["id"] is str

    @pytest.mark.unit
    def test_has_date_field(self) -> None:
        """date フィールド（YYYY-MM-DD 文字列、YAML serializable）"""
        hints = get_type_hints(RawEntry)
        assert "date" in hints
        assert hints["date"] is str

    @pytest.mark.unit
    def test_has_time_field(self) -> None:
        """time フィールド（HH:MM:SS 文字列）"""
        hints = get_type_hints(RawEntry)
        assert "time" in hints
        assert hints["time"] is str

    @pytest.mark.unit
    def test_has_source_type_field(self) -> None:
        """source_type フィールド（"email" 等のソース種別）"""
        hints = get_type_hints(RawEntry)
        assert "source_type" in hints
        assert hints["source_type"] is str

    @pytest.mark.unit
    def test_has_from_addr_field(self) -> None:
        """from_addr フィールド（送信者アドレス文字列）"""
        hints = get_type_hints(RawEntry)
        assert "from_addr" in hints
        assert hints["from_addr"] is str

    @pytest.mark.unit
    def test_has_to_addrs_field(self) -> None:
        """to_addrs フィールド（宛先アドレス文字列リスト）"""
        hints = get_type_hints(RawEntry)
        assert "to_addrs" in hints
        assert hints["to_addrs"] == List[str]

    @pytest.mark.unit
    def test_has_cc_addrs_field(self) -> None:
        """cc_addrs フィールド（CC アドレス文字列リスト）"""
        hints = get_type_hints(RawEntry)
        assert "cc_addrs" in hints
        assert hints["cc_addrs"] == List[str]

    @pytest.mark.unit
    def test_has_subject_field(self) -> None:
        """subject フィールド（件名）"""
        hints = get_type_hints(RawEntry)
        assert "subject" in hints
        assert hints["subject"] is str

    @pytest.mark.unit
    def test_has_thread_id_field(self) -> None:
        """thread_id フィールド（None 許容）"""
        hints = get_type_hints(RawEntry)
        assert "thread_id" in hints
        assert hints["thread_id"] == Optional[str]

    @pytest.mark.unit
    def test_has_attachments_field(self) -> None:
        """attachments フィールド（ファイル名リスト、内容は保持しない）"""
        hints = get_type_hints(RawEntry)
        assert "attachments" in hints
        assert hints["attachments"] == List[str]

    @pytest.mark.unit
    def test_has_tags_field(self) -> None:
        """tags フィールド（triage 後に付与されるタグ）"""
        hints = get_type_hints(RawEntry)
        assert "tags" in hints
        assert hints["tags"] == List[str]

    @pytest.mark.unit
    def test_has_body_field(self) -> None:
        """body フィールド（プレーンテキスト本文）"""
        hints = get_type_hints(RawEntry)
        assert "body" in hints
        assert hints["body"] is str

    @pytest.mark.unit
    def test_can_construct_minimal(self) -> None:
        """業務計画書 §4.1 のサンプル相当で構築可能"""
        entry: RawEntry = {
            "id": "email_20260407_143022_abc123",
            "date": "2026-04-07",
            "time": "14:30:22",
            "source_type": "email",
            "from_addr": "ichikawa@meguru.co.jp",
            "to_addrs": ["oowanushi@meguru.co.jp"],
            "cc_addrs": ["honma@meguru.co.jp"],
            "subject": "○○マンション新築工事 排煙設備について",
            "thread_id": "thread_xyz789",
            "attachments": ["排煙計算書.pdf"],
            "tags": [],
            "body": "市川です。お疲れ様です。",
        }
        assert entry["id"] == "email_20260407_143022_abc123"
        assert entry["thread_id"] == "thread_xyz789"
        assert entry["tags"] == []

    @pytest.mark.unit
    def test_can_construct_without_thread(self) -> None:
        """thread_id None で構築可能（スレッド未推定エントリ）"""
        entry: RawEntry = {
            "id": "email_20260407_100000_def456",
            "date": "2026-04-07",
            "time": "10:00:00",
            "source_type": "email",
            "from_addr": "noreply@example.com",
            "to_addrs": ["info@meguru.co.jp"],
            "cc_addrs": [],
            "subject": "通知",
            "thread_id": None,
            "attachments": [],
            "tags": [],
            "body": "",
        }
        assert entry["thread_id"] is None
        assert entry["body"] == ""

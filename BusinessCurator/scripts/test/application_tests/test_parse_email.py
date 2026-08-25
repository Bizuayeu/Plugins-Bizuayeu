#!/usr/bin/env python3
"""
application/ingest/parse_email.py テスト
=========================================

ParseEmailUseCase の EmailMessage → RawEntry 変換検証。

設計意図:
- ParseEmailUseCase は純粋変換ロジック（I/O なし）
- EmailMessage を input、RawEntry を output
- 添付ファイルは filename のみ抽出（バイナリは保持しない）
- thread_id は in_reply_to / references から推定（パーサー出力の優先）
"""

from datetime import datetime

import pytest

from application.ingest.parse_email import ParseEmailUseCase
from domain.types.entry import RawEntry
from test.test_helpers import build_email_message

# =============================================================================
# 基本変換
# =============================================================================


class TestParseEmailUseCaseBasic:
    """基本的な EmailMessage → RawEntry 変換"""

    @pytest.mark.unit
    def test_returns_raw_entry(self) -> None:
        msg = build_email_message()
        usecase = ParseEmailUseCase()
        result = usecase.execute(msg)
        # RawEntry の必須フィールドが揃っていること
        assert "id" in result
        assert result["source_type"] == "email"

    @pytest.mark.unit
    def test_id_is_deterministic(self) -> None:
        """同じ入力なら同じ ID（冪等性）"""
        msg = build_email_message(message_id="<abc@x>")
        usecase = ParseEmailUseCase()
        r1 = usecase.execute(msg)
        r2 = usecase.execute(msg)
        assert r1["id"] == r2["id"]

    @pytest.mark.unit
    def test_id_starts_with_email_prefix(self) -> None:
        msg = build_email_message()
        result = ParseEmailUseCase().execute(msg)
        assert result["id"].startswith("email_")

    @pytest.mark.unit
    def test_date_and_time_extracted_from_datetime(self) -> None:
        msg = build_email_message(date=datetime(2026, 4, 7, 14, 30, 22))
        result = ParseEmailUseCase().execute(msg)
        assert result["date"] == "2026-04-07"
        assert result["time"] == "14:30:22"

    @pytest.mark.unit
    def test_from_addr_serialized(self) -> None:
        msg = build_email_message(from_address="sender@example.com")
        result = ParseEmailUseCase().execute(msg)
        assert result["from_addr"] == "sender@example.com"

    @pytest.mark.unit
    def test_to_addrs_serialized_as_strings(self) -> None:
        msg = build_email_message(to_addresses=["a@x", "b@y"])
        result = ParseEmailUseCase().execute(msg)
        assert result["to_addrs"] == ["a@x", "b@y"]

    @pytest.mark.unit
    def test_cc_addrs_serialized(self) -> None:
        msg = build_email_message(cc_addresses=["c@x"])
        result = ParseEmailUseCase().execute(msg)
        assert result["cc_addrs"] == ["c@x"]

    @pytest.mark.unit
    def test_subject_preserved(self) -> None:
        msg = build_email_message(subject="○○マンション排煙設備")
        result = ParseEmailUseCase().execute(msg)
        assert result["subject"] == "○○マンション排煙設備"

    @pytest.mark.unit
    def test_body_extracted_from_text(self) -> None:
        msg = build_email_message(body_text="本文です")
        result = ParseEmailUseCase().execute(msg)
        assert result["body"] == "本文です"

    @pytest.mark.unit
    def test_initial_tags_empty(self) -> None:
        """生成直後 tags は空（triage 後に付与される）"""
        msg = build_email_message()
        result = ParseEmailUseCase().execute(msg)
        assert result["tags"] == []


# =============================================================================
# 添付ファイル
# =============================================================================


class TestParseEmailUseCaseAttachments:
    """添付ファイル処理"""

    @pytest.mark.unit
    def test_attachment_filenames_extracted(self) -> None:
        msg = build_email_message(
            attachments=[
                {
                    "filename": "排煙計算書.pdf",
                    "content_type": "application/pdf",
                    "size": 1024,
                },
                {
                    "filename": "図面.dwg",
                    "content_type": "application/octet-stream",
                    "size": 2048,
                },
            ]
        )
        result = ParseEmailUseCase().execute(msg)
        assert result["attachments"] == ["排煙計算書.pdf", "図面.dwg"]

    @pytest.mark.unit
    def test_no_attachments(self) -> None:
        msg = build_email_message()
        result = ParseEmailUseCase().execute(msg)
        assert result["attachments"] == []


# =============================================================================
# thread_id 推定
# =============================================================================


class TestParseEmailUseCaseThreadId:
    """thread_id の決定ロジック"""

    @pytest.mark.unit
    def test_explicit_thread_id_preserved(self) -> None:
        """パーサーが thread_id を提供している場合はそれを使う"""
        msg = build_email_message(thread_id="thread_xyz")
        result = ParseEmailUseCase().execute(msg)
        assert result["thread_id"] == "thread_xyz"

    @pytest.mark.unit
    def test_thread_id_from_in_reply_to(self) -> None:
        """thread_id 未提供なら in_reply_to を thread_id 代わりに使う"""
        msg = build_email_message(thread_id=None, in_reply_to="<parent@x>")
        result = ParseEmailUseCase().execute(msg)
        assert result["thread_id"] == "<parent@x>"

    @pytest.mark.unit
    def test_thread_id_from_references_root(self) -> None:
        """in_reply_to がなく references があればその先頭"""
        msg = build_email_message(
            thread_id=None,
            in_reply_to=None,
            references=["<root@x>", "<mid@x>"],
        )
        result = ParseEmailUseCase().execute(msg)
        assert result["thread_id"] == "<root@x>"

    @pytest.mark.unit
    def test_thread_id_none_when_no_hints(self) -> None:
        """すべてなければ None"""
        msg = build_email_message(thread_id=None, in_reply_to=None, references=[])
        result = ParseEmailUseCase().execute(msg)
        assert result["thread_id"] is None


# =============================================================================
# 検証パス
# =============================================================================


class TestParseEmailUseCaseValidation:
    """生成された RawEntry が validate_raw_entry を満たす"""

    @pytest.mark.unit
    def test_output_passes_validation(self) -> None:
        from domain.validation import validate_raw_entry

        msg = build_email_message()
        result = ParseEmailUseCase().execute(msg)
        validate_raw_entry(result)  # 例外なし

#!/usr/bin/env python3
"""
application/fetch/fetch_batch.py テスト
=======================================
"""

from datetime import date, datetime, timezone

import pytest

from application.fetch.fetch_batch import STATE_SAVE_INTERVAL, FetchBatchUseCase
from domain.exceptions import InvalidBackupPlanError
from domain.types.account import GmailAccount
from domain.types.backup import BackupPlan, BackupState
from domain.types.query import SearchQuery
from test.test_helpers import (
    FakeClock,
    FakeGmailClient,
    FakeMessageWriter,
    FakeStateRepository,
    make_gmail_message,
)


def _sample_account() -> GmailAccount:
    return {
        "email": "togami-log@meguru-construction.example.jp",
        "label": "togami-log",
        "credentials_path": "/tmp/cs.json",
        "token_path": "/tmp/tok.json",
    }


def _sample_query() -> SearchQuery:
    return {
        "from_addr": None,
        "to_addr": None,
        "subject": None,
        "label": None,
        "date_range": {"start": date(2026, 4, 1), "end": date(2026, 4, 12)},
        "has_attachment": None,
        "raw_query": None,
    }


def _sample_plan(output_format: str = "eml") -> BackupPlan:
    return {
        "plan_id": "plan_20260411_test0001",
        "account": _sample_account(),
        "query": _sample_query(),
        "output_dir": "/tmp/output",
        "output_format": output_format,  # type: ignore[typeddict-item]
    }


# =============================================================================
# Validation
# =============================================================================


class TestPlanValidation:
    @pytest.mark.unit
    def test_empty_plan_id_raises(self) -> None:
        uc = FetchBatchUseCase(
            FakeGmailClient(), FakeMessageWriter(), FakeStateRepository(), FakeClock()
        )
        plan = _sample_plan()
        plan["plan_id"] = ""
        with pytest.raises(InvalidBackupPlanError, match="plan_id"):
            uc.execute(plan, state_dir="/tmp/state")

    @pytest.mark.unit
    def test_empty_output_dir_raises(self) -> None:
        uc = FetchBatchUseCase(
            FakeGmailClient(), FakeMessageWriter(), FakeStateRepository(), FakeClock()
        )
        plan = _sample_plan()
        plan["output_dir"] = ""
        with pytest.raises(InvalidBackupPlanError, match="output_dir"):
            uc.execute(plan, state_dir="/tmp/state")

    @pytest.mark.unit
    def test_invalid_format_raises(self) -> None:
        uc = FetchBatchUseCase(
            FakeGmailClient(), FakeMessageWriter(), FakeStateRepository(), FakeClock()
        )
        plan = _sample_plan()
        plan["output_format"] = "txt"  # type: ignore[typeddict-item]
        with pytest.raises(InvalidBackupPlanError, match="output_format"):
            uc.execute(plan, state_dir="/tmp/state")


# =============================================================================
# Happy path: empty & small & resume
# =============================================================================


class TestFetchBatch:
    @pytest.mark.unit
    def test_empty_gmail_returns_zero_counts(self) -> None:
        client = FakeGmailClient(messages=[])
        writer = FakeMessageWriter()
        state_repo = FakeStateRepository()
        clock = FakeClock()
        uc = FetchBatchUseCase(client, writer, state_repo, clock)

        result = uc.execute(_sample_plan(), state_dir="/tmp/state")

        assert result["success_count"] == 0
        assert result["failure_count"] == 0
        assert result["output_files"] == []

    @pytest.mark.unit
    def test_single_message_written(self) -> None:
        client = FakeGmailClient(messages=[make_gmail_message("id1")])
        writer = FakeMessageWriter()
        state_repo = FakeStateRepository()
        clock = FakeClock()
        uc = FetchBatchUseCase(client, writer, state_repo, clock)

        result = uc.execute(_sample_plan(), state_dir="/tmp/state")

        assert result["success_count"] == 1
        assert result["failure_count"] == 0
        assert len(writer.written) == 1
        assert writer.written[0]["gmail_id"] == "id1"

    @pytest.mark.unit
    def test_multiple_messages_all_written(self) -> None:
        messages = [make_gmail_message(f"id{i}") for i in range(5)]
        client = FakeGmailClient(messages=messages)
        writer = FakeMessageWriter()
        state_repo = FakeStateRepository()
        clock = FakeClock()
        uc = FetchBatchUseCase(client, writer, state_repo, clock)

        result = uc.execute(_sample_plan(), state_dir="/tmp/state")

        assert result["success_count"] == 5
        assert len(writer.written) == 5

    @pytest.mark.unit
    def test_uses_gmail_query_string(self) -> None:
        """Gmail client.list_message_ids がクエリ文字列で呼ばれる"""
        client = FakeGmailClient(messages=[])
        uc = FetchBatchUseCase(client, FakeMessageWriter(), FakeStateRepository(), FakeClock())

        uc.execute(_sample_plan(), state_dir="/tmp/state")

        assert len(client.list_calls) == 1
        assert "after:2026/04/01" in client.list_calls[0]
        assert "before:2026/04/12" in client.list_calls[0]

    @pytest.mark.unit
    def test_writer_finalize_called(self) -> None:
        writer = FakeMessageWriter()
        uc = FetchBatchUseCase(FakeGmailClient(), writer, FakeStateRepository(), FakeClock())

        uc.execute(_sample_plan(), state_dir="/tmp/state")

        assert writer.finalized is True


# =============================================================================
# Resume
# =============================================================================


class TestResume:
    @pytest.mark.unit
    def test_resume_skips_already_fetched(self) -> None:
        """既存state の fetched_ids にある ID は再取得しない"""
        messages = [make_gmail_message(f"id{i}") for i in range(5)]
        client = FakeGmailClient(messages=messages)
        writer = FakeMessageWriter()
        state_repo = FakeStateRepository()
        clock = FakeClock()

        # 既存 state をセット（3件取得済み）
        existing_state: BackupState = {
            "plan_id": "plan_20260411_test0001",
            "fetched_ids": ["id0", "id1", "id2"],
            "failed_ids": [],
            "last_updated": datetime(2026, 4, 11, 9, 0, 0, tzinfo=timezone.utc),
            "total_estimated": 5,
        }
        state_repo.save(existing_state, "/tmp/state")

        uc = FetchBatchUseCase(client, writer, state_repo, clock)
        result = uc.execute(_sample_plan(), state_dir="/tmp/state", resume=True)

        # 新規取得は 2件 (id3, id4) のみ
        assert result["success_count"] == 2
        assert len(writer.written) == 2
        fetched_ids_in_writer = {m["gmail_id"] for m in writer.written}
        assert fetched_ids_in_writer == {"id3", "id4"}

    @pytest.mark.unit
    def test_resume_false_ignores_existing_state(self) -> None:
        messages = [make_gmail_message(f"id{i}") for i in range(3)]
        client = FakeGmailClient(messages=messages)
        writer = FakeMessageWriter()
        state_repo = FakeStateRepository()

        existing_state: BackupState = {
            "plan_id": "plan_20260411_test0001",
            "fetched_ids": ["id0", "id1"],
            "failed_ids": [],
            "last_updated": datetime(2026, 4, 11, 9, 0, 0, tzinfo=timezone.utc),
            "total_estimated": 3,
        }
        state_repo.save(existing_state, "/tmp/state")

        uc = FetchBatchUseCase(client, writer, state_repo, FakeClock())
        result = uc.execute(_sample_plan(), state_dir="/tmp/state", resume=False)

        # 全件を新規取得
        assert result["success_count"] == 3


# =============================================================================
# Failures
# =============================================================================


class TestFailures:
    @pytest.mark.unit
    def test_fetch_failure_continues_batch(self) -> None:
        messages = [make_gmail_message(f"id{i}") for i in range(3)]
        client = FakeGmailClient(messages=messages, fetch_failures={"id1"})
        writer = FakeMessageWriter()
        uc = FetchBatchUseCase(client, writer, FakeStateRepository(), FakeClock())

        result = uc.execute(_sample_plan(), state_dir="/tmp/state")

        assert result["success_count"] == 2
        assert result["failure_count"] == 1

    @pytest.mark.unit
    def test_writer_failure_continues_batch(self) -> None:
        messages = [make_gmail_message(f"id{i}") for i in range(3)]
        client = FakeGmailClient(messages=messages)
        writer = FakeMessageWriter(fail_on={"id2"})
        uc = FetchBatchUseCase(client, writer, FakeStateRepository(), FakeClock())

        result = uc.execute(_sample_plan(), state_dir="/tmp/state")

        assert result["success_count"] == 2
        assert result["failure_count"] == 1

    @pytest.mark.unit
    def test_failed_ids_saved_to_state(self) -> None:
        messages = [make_gmail_message(f"id{i}") for i in range(3)]
        client = FakeGmailClient(messages=messages, fetch_failures={"id1"})
        state_repo = FakeStateRepository()
        uc = FetchBatchUseCase(client, FakeMessageWriter(), state_repo, FakeClock())

        uc.execute(_sample_plan(), state_dir="/tmp/state")

        saved = state_repo.load("plan_20260411_test0001", "/tmp/state")
        assert saved is not None
        assert "id1" in saved["failed_ids"]


# =============================================================================
# max_messages
# =============================================================================


class TestMaxMessages:
    @pytest.mark.unit
    def test_max_messages_limits_success_count(self) -> None:
        messages = [make_gmail_message(f"id{i}") for i in range(20)]
        client = FakeGmailClient(messages=messages)
        writer = FakeMessageWriter()
        uc = FetchBatchUseCase(client, writer, FakeStateRepository(), FakeClock())

        result = uc.execute(_sample_plan(), state_dir="/tmp/state", max_messages=5)

        assert result["success_count"] == 5
        assert len(writer.written) == 5


# =============================================================================
# State persistence
# =============================================================================


class TestStatePersistence:
    @pytest.mark.unit
    def test_state_saved_at_end_with_all_fetched_ids(self) -> None:
        messages = [make_gmail_message(f"id{i}") for i in range(3)]
        client = FakeGmailClient(messages=messages)
        state_repo = FakeStateRepository()
        uc = FetchBatchUseCase(client, FakeMessageWriter(), state_repo, FakeClock())

        uc.execute(_sample_plan(), state_dir="/tmp/state")

        saved = state_repo.load("plan_20260411_test0001", "/tmp/state")
        assert saved is not None
        assert set(saved["fetched_ids"]) == {"id0", "id1", "id2"}
        assert saved["total_estimated"] == 3

    @pytest.mark.unit
    def test_state_save_interval_reduces_io(self) -> None:
        """STATE_SAVE_INTERVAL 件ごとに state_repo.save が呼ばれる（最終保存除く）"""
        count = STATE_SAVE_INTERVAL * 2 + 3
        messages = [make_gmail_message(f"id{i}") for i in range(count)]
        client = FakeGmailClient(messages=messages)
        state_repo = FakeStateRepository()
        uc = FetchBatchUseCase(client, FakeMessageWriter(), state_repo, FakeClock())

        uc.execute(_sample_plan(), state_dir="/tmp/state")

        # 中間保存 2回 + 最終保存 1回 = 3回以上（estimate_countのtry/exceptで追加される可能性）
        assert state_repo.save_count >= 3

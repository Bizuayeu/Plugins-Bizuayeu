#!/usr/bin/env python3
"""
domain/types/multi_backup.py テスト
===================================
"""

from datetime import date, datetime, timezone
from typing import get_type_hints

import pytest

from domain.types.account import GmailAccount
from domain.types.backup import BackupState
from domain.types.multi_backup import (
    MultiUserBackupPlan,
    MultiUserBackupResult,
    MultiUserBackupState,
)
from domain.types.query import SearchQuery


def _sample_account(email: str) -> GmailAccount:
    return {
        "email": email,
        "label": email.split("@")[0],
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


def _sample_single_state(plan_id: str) -> BackupState:
    return {
        "plan_id": plan_id,
        "fetched_ids": [],
        "failed_ids": [],
        "last_updated": datetime(2026, 4, 11, 10, 0, tzinfo=timezone.utc),
        "total_estimated": 0,
    }


# =============================================================================
# MultiUserBackupPlan
# =============================================================================


class TestMultiUserBackupPlan:
    @pytest.mark.unit
    def test_has_all_required_fields(self) -> None:
        hints = get_type_hints(MultiUserBackupPlan)
        for field in ["multi_plan_id", "accounts", "query", "output_dir", "output_format"]:
            assert field in hints

    @pytest.mark.unit
    def test_can_construct_multi_user_plan(self) -> None:
        plan: MultiUserBackupPlan = {
            "multi_plan_id": "multi_plan_20260411_abcd",
            "accounts": [
                _sample_account("alice@meguru.example.jp"),
                _sample_account("bob@meguru.example.jp"),
            ],
            "query": _sample_query(),
            "output_dir": "/path/to/output",
            "output_format": "eml",
        }
        assert len(plan["accounts"]) == 2
        assert plan["accounts"][0]["email"] == "alice@meguru.example.jp"

    @pytest.mark.unit
    def test_supports_mbox_format(self) -> None:
        plan: MultiUserBackupPlan = {
            "multi_plan_id": "x",
            "accounts": [_sample_account("a@b.com")],
            "query": _sample_query(),
            "output_dir": "/tmp",
            "output_format": "mbox",
        }
        assert plan["output_format"] == "mbox"


# =============================================================================
# MultiUserBackupState
# =============================================================================


class TestMultiUserBackupState:
    @pytest.mark.unit
    def test_has_all_required_fields(self) -> None:
        hints = get_type_hints(MultiUserBackupState)
        for field in [
            "multi_plan_id",
            "per_user_states",
            "message_id_index",
            "last_updated",
            "started_user_emails",
            "completed_user_emails",
        ]:
            assert field in hints

    @pytest.mark.unit
    def test_can_construct_empty_initial_state(self) -> None:
        state: MultiUserBackupState = {
            "multi_plan_id": "multi_plan_20260411_abcd",
            "per_user_states": {},
            "message_id_index": {},
            "last_updated": datetime(2026, 4, 11, 10, 0, tzinfo=timezone.utc),
            "started_user_emails": [],
            "completed_user_emails": [],
        }
        assert state["per_user_states"] == {}
        assert state["message_id_index"] == {}

    @pytest.mark.unit
    def test_tracks_message_id_to_owner_mapping(self) -> None:
        """message_id_index は normalized Message-ID → "email::gmail_id" のマップ"""
        state: MultiUserBackupState = {
            "multi_plan_id": "x",
            "per_user_states": {},
            "message_id_index": {
                "<abc@example.com>": "alice@meguru.example.jp::gmail_id_1",
                "<def@example.com>": "bob@meguru.example.jp::gmail_id_2",
            },
            "last_updated": datetime(2026, 4, 11, tzinfo=timezone.utc),
            "started_user_emails": [],
            "completed_user_emails": [],
        }
        assert (
            state["message_id_index"]["<abc@example.com>"] == "alice@meguru.example.jp::gmail_id_1"
        )

    @pytest.mark.unit
    def test_can_nest_single_user_states(self) -> None:
        """per_user_states は既存 BackupState を内包する"""
        single = _sample_single_state("multi_plan_20260411_abcd__alice")
        state: MultiUserBackupState = {
            "multi_plan_id": "multi_plan_20260411_abcd",
            "per_user_states": {"alice@meguru.example.jp": single},
            "message_id_index": {},
            "last_updated": datetime(2026, 4, 11, tzinfo=timezone.utc),
            "started_user_emails": ["alice@meguru.example.jp"],
            "completed_user_emails": [],
        }
        assert (
            state["per_user_states"]["alice@meguru.example.jp"]["plan_id"]
            == "multi_plan_20260411_abcd__alice"
        )


# =============================================================================
# MultiUserBackupResult
# =============================================================================


class TestMultiUserBackupResult:
    @pytest.mark.unit
    def test_has_all_required_fields(self) -> None:
        hints = get_type_hints(MultiUserBackupResult)
        for field in [
            "multi_plan_id",
            "per_user_success",
            "per_user_failure",
            "per_user_deduped",
            "total_unique_messages",
            "total_dedup_skipped",
            "total_messages_without_message_id",
            "output_files",
            "started_at",
            "finished_at",
        ]:
            assert field in hints

    @pytest.mark.unit
    def test_can_construct_result(self) -> None:
        result: MultiUserBackupResult = {
            "multi_plan_id": "multi_plan_20260411_abcd",
            "per_user_success": {"alice@meguru.example.jp": 50, "bob@meguru.example.jp": 12},
            "per_user_failure": {"alice@meguru.example.jp": 0, "bob@meguru.example.jp": 1},
            "per_user_deduped": {"alice@meguru.example.jp": 0, "bob@meguru.example.jp": 38},
            "total_unique_messages": 62,
            "total_dedup_skipped": 38,
            "total_messages_without_message_id": 2,
            "output_files": ["/path/f1.eml", "/path/f2.eml"],
            "started_at": datetime(2026, 4, 11, 10, 0, tzinfo=timezone.utc),
            "finished_at": datetime(2026, 4, 11, 10, 30, tzinfo=timezone.utc),
        }
        assert result["total_unique_messages"] == 62
        assert result["total_dedup_skipped"] == 38

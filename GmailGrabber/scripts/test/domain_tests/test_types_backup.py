#!/usr/bin/env python3
"""
domain/types/backup.py テスト
=============================

BackupPlan / BackupState / BackupResult / OutputFormat TypedDict の検証。
"""

from datetime import date, datetime, timezone
from typing import get_type_hints

import pytest

from domain.types.account import GmailAccount
from domain.types.backup import BackupPlan, BackupResult, BackupState
from domain.types.query import SearchQuery


def _sample_account() -> GmailAccount:
    return {
        "email": "togami-log@meguru-construction.com",
        "label": "togami-log",
        "credentials_path": "/tmp/client_secret.json",
        "token_path": "/tmp/token.json",
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


# =============================================================================
# BackupPlan
# =============================================================================


class TestBackupPlan:
    @pytest.mark.unit
    def test_has_all_required_fields(self) -> None:
        hints = get_type_hints(BackupPlan)
        assert "plan_id" in hints
        assert "account" in hints
        assert "query" in hints
        assert "output_dir" in hints
        assert "output_format" in hints

    @pytest.mark.unit
    def test_can_construct_eml_plan(self) -> None:
        plan: BackupPlan = {
            "plan_id": "plan_20260411_abcd",
            "account": _sample_account(),
            "query": _sample_query(),
            "output_dir": "/path/to/BusinessWiki/data/2026-04",
            "output_format": "eml",
        }
        assert plan["output_format"] == "eml"
        assert plan["account"]["email"] == "togami-log@meguru-construction.com"

    @pytest.mark.unit
    def test_can_construct_mbox_plan(self) -> None:
        plan: BackupPlan = {
            "plan_id": "plan_20260411_efgh",
            "account": _sample_account(),
            "query": _sample_query(),
            "output_dir": "/path/to/BusinessWiki/data/2026-04",
            "output_format": "mbox",
        }
        assert plan["output_format"] == "mbox"


# =============================================================================
# BackupState
# =============================================================================


class TestBackupState:
    @pytest.mark.unit
    def test_has_all_required_fields(self) -> None:
        hints = get_type_hints(BackupState)
        assert "plan_id" in hints
        assert "fetched_ids" in hints
        assert "failed_ids" in hints
        assert "last_updated" in hints
        assert "total_estimated" in hints

    @pytest.mark.unit
    def test_can_construct_initial_state(self) -> None:
        state: BackupState = {
            "plan_id": "plan_20260411_abcd",
            "fetched_ids": [],
            "failed_ids": [],
            "last_updated": datetime(2026, 4, 11, 10, 0, tzinfo=timezone.utc),
            "total_estimated": 0,
        }
        assert state["fetched_ids"] == []
        assert state["total_estimated"] == 0

    @pytest.mark.unit
    def test_can_track_progress(self) -> None:
        state: BackupState = {
            "plan_id": "plan_20260411_abcd",
            "fetched_ids": ["id1", "id2", "id3"],
            "failed_ids": ["id4"],
            "last_updated": datetime(2026, 4, 11, 10, 5, tzinfo=timezone.utc),
            "total_estimated": 100,
        }
        assert len(state["fetched_ids"]) == 3
        assert len(state["failed_ids"]) == 1


# =============================================================================
# BackupResult
# =============================================================================


class TestBackupResult:
    @pytest.mark.unit
    def test_has_all_required_fields(self) -> None:
        hints = get_type_hints(BackupResult)
        assert "plan_id" in hints
        assert "success_count" in hints
        assert "failure_count" in hints
        assert "output_files" in hints
        assert "started_at" in hints
        assert "finished_at" in hints

    @pytest.mark.unit
    def test_can_construct_result(self) -> None:
        result: BackupResult = {
            "plan_id": "plan_20260411_abcd",
            "success_count": 42,
            "failure_count": 0,
            "output_files": ["/path/to/email1.eml", "/path/to/email2.eml"],
            "started_at": datetime(2026, 4, 11, 10, 0, tzinfo=timezone.utc),
            "finished_at": datetime(2026, 4, 11, 10, 30, tzinfo=timezone.utc),
        }
        assert result["success_count"] == 42
        assert result["failure_count"] == 0

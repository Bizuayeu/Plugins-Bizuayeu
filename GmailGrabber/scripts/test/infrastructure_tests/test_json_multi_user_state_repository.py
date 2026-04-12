#!/usr/bin/env python3
"""
infrastructure/repositories/json_multi_user_state_repository.py テスト
======================================================================
"""

from datetime import datetime, timezone
from pathlib import Path

import pytest

from domain.types.backup import BackupState
from domain.types.multi_backup import MultiUserBackupState
from infrastructure.repositories.json_multi_user_state_repository import (
    JsonMultiUserStateRepository,
)


def _sample_single_state(plan_id: str) -> BackupState:
    return {
        "plan_id": plan_id,
        "fetched_ids": ["id1", "id2"],
        "failed_ids": ["id3"],
        "last_updated": datetime(2026, 4, 11, 10, 0, tzinfo=timezone.utc),
        "total_estimated": 50,
    }


def _sample_multi_state() -> MultiUserBackupState:
    return {
        "multi_plan_id": "multi_plan_20260411_abcdefghij",
        "per_user_states": {
            "alice@m.com": _sample_single_state("multi_plan_20260411_abcdefghij__alice"),
            "bob@m.com": _sample_single_state("multi_plan_20260411_abcdefghij__bob"),
        },
        "message_id_index": {
            "<msg1@ex.com>": "alice@m.com::id1",
            "<msg2@ex.com>": "bob@m.com::id1",
        },
        "last_updated": datetime(2026, 4, 11, 10, 30, tzinfo=timezone.utc),
        "started_user_emails": ["alice@m.com", "bob@m.com"],
        "completed_user_emails": ["alice@m.com"],
    }


class TestSaveLoad:
    @pytest.mark.integration
    def test_load_nonexistent_returns_none(self, tmp_path: Path) -> None:
        repo = JsonMultiUserStateRepository()
        result = repo.load("missing_plan", str(tmp_path))
        assert result is None

    @pytest.mark.integration
    def test_save_load_roundtrip(self, tmp_path: Path) -> None:
        repo = JsonMultiUserStateRepository()
        state = _sample_multi_state()

        repo.save(state, str(tmp_path))
        loaded = repo.load("multi_plan_20260411_abcdefghij", str(tmp_path))

        assert loaded is not None
        assert loaded["multi_plan_id"] == state["multi_plan_id"]
        assert loaded["last_updated"] == state["last_updated"]

    @pytest.mark.integration
    def test_per_user_states_roundtrip(self, tmp_path: Path) -> None:
        repo = JsonMultiUserStateRepository()
        state = _sample_multi_state()
        repo.save(state, str(tmp_path))

        loaded = repo.load("multi_plan_20260411_abcdefghij", str(tmp_path))

        assert loaded is not None
        assert "alice@m.com" in loaded["per_user_states"]
        assert "bob@m.com" in loaded["per_user_states"]
        assert loaded["per_user_states"]["alice@m.com"]["fetched_ids"] == ["id1", "id2"]
        assert loaded["per_user_states"]["alice@m.com"]["failed_ids"] == ["id3"]

    @pytest.mark.integration
    def test_message_id_index_preserved(self, tmp_path: Path) -> None:
        repo = JsonMultiUserStateRepository()
        state = _sample_multi_state()
        repo.save(state, str(tmp_path))

        loaded = repo.load("multi_plan_20260411_abcdefghij", str(tmp_path))

        assert loaded is not None
        assert loaded["message_id_index"] == state["message_id_index"]

    @pytest.mark.integration
    def test_started_and_completed_lists_preserved(self, tmp_path: Path) -> None:
        repo = JsonMultiUserStateRepository()
        state = _sample_multi_state()
        repo.save(state, str(tmp_path))

        loaded = repo.load("multi_plan_20260411_abcdefghij", str(tmp_path))

        assert loaded is not None
        assert loaded["started_user_emails"] == ["alice@m.com", "bob@m.com"]
        assert loaded["completed_user_emails"] == ["alice@m.com"]

    @pytest.mark.integration
    def test_save_creates_state_dir(self, tmp_path: Path) -> None:
        repo = JsonMultiUserStateRepository()
        nested = tmp_path / "deep" / "state"
        repo.save(_sample_multi_state(), str(nested))
        assert nested.exists()

    @pytest.mark.integration
    def test_state_file_name_contains_multi_plan_id(self, tmp_path: Path) -> None:
        repo = JsonMultiUserStateRepository()
        repo.save(_sample_multi_state(), str(tmp_path))
        files = list(tmp_path.glob("multi_state_*.json"))
        assert len(files) == 1
        assert "multi_plan_20260411_abcdefghij" in files[0].name

    @pytest.mark.integration
    def test_save_overwrites(self, tmp_path: Path) -> None:
        repo = JsonMultiUserStateRepository()
        state = _sample_multi_state()
        repo.save(state, str(tmp_path))

        # 更新
        state["completed_user_emails"] = ["alice@m.com", "bob@m.com"]
        repo.save(state, str(tmp_path))

        loaded = repo.load("multi_plan_20260411_abcdefghij", str(tmp_path))
        assert loaded is not None
        assert loaded["completed_user_emails"] == ["alice@m.com", "bob@m.com"]

    @pytest.mark.integration
    def test_delete_removes_file(self, tmp_path: Path) -> None:
        repo = JsonMultiUserStateRepository()
        repo.save(_sample_multi_state(), str(tmp_path))
        repo.delete("multi_plan_20260411_abcdefghij", str(tmp_path))
        assert repo.load("multi_plan_20260411_abcdefghij", str(tmp_path)) is None

    @pytest.mark.integration
    def test_delete_nonexistent_is_noop(self, tmp_path: Path) -> None:
        repo = JsonMultiUserStateRepository()
        repo.delete("missing", str(tmp_path))

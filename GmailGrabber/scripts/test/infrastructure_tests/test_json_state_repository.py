#!/usr/bin/env python3
"""
infrastructure/repositories/json_state_repository.py テスト
===========================================================
"""

from datetime import datetime, timezone
from pathlib import Path

import pytest

from domain.types.backup import BackupState
from infrastructure.repositories.json_state_repository import JsonStateRepository


def _sample_state() -> BackupState:
    return {
        "plan_id": "plan_20260411_abcd",
        "fetched_ids": ["id1", "id2", "id3"],
        "failed_ids": ["id4"],
        "last_updated": datetime(2026, 4, 11, 10, 30, tzinfo=timezone.utc),
        "total_estimated": 100,
    }


class TestJsonStateRepository:
    @pytest.mark.integration
    def test_load_nonexistent_returns_none(self, tmp_path: Path) -> None:
        repo = JsonStateRepository()
        result = repo.load("missing_plan", str(tmp_path))
        assert result is None

    @pytest.mark.integration
    def test_save_and_load_roundtrip(self, tmp_path: Path) -> None:
        repo = JsonStateRepository()
        state = _sample_state()

        repo.save(state, str(tmp_path))
        loaded = repo.load("plan_20260411_abcd", str(tmp_path))

        assert loaded is not None
        assert loaded["plan_id"] == state["plan_id"]
        assert loaded["fetched_ids"] == state["fetched_ids"]
        assert loaded["failed_ids"] == state["failed_ids"]
        assert loaded["total_estimated"] == state["total_estimated"]
        assert loaded["last_updated"] == state["last_updated"]

    @pytest.mark.integration
    def test_save_creates_state_dir(self, tmp_path: Path) -> None:
        repo = JsonStateRepository()
        nested = tmp_path / "nested" / "state"

        repo.save(_sample_state(), str(nested))

        assert nested.exists()
        assert (nested / "state_plan_20260411_abcd.json").exists()

    @pytest.mark.integration
    def test_save_overwrites(self, tmp_path: Path) -> None:
        repo = JsonStateRepository()
        initial = _sample_state()
        repo.save(initial, str(tmp_path))

        updated = {**initial, "fetched_ids": ["id1", "id2", "id3", "id5"]}
        repo.save(updated, str(tmp_path))  # type: ignore[arg-type]

        loaded = repo.load("plan_20260411_abcd", str(tmp_path))
        assert loaded is not None
        assert loaded["fetched_ids"] == ["id1", "id2", "id3", "id5"]

    @pytest.mark.integration
    def test_delete_existing(self, tmp_path: Path) -> None:
        repo = JsonStateRepository()
        repo.save(_sample_state(), str(tmp_path))

        repo.delete("plan_20260411_abcd", str(tmp_path))

        assert repo.load("plan_20260411_abcd", str(tmp_path)) is None

    @pytest.mark.integration
    def test_delete_nonexistent_is_noop(self, tmp_path: Path) -> None:
        repo = JsonStateRepository()
        # エラーにならないこと
        repo.delete("missing", str(tmp_path))

#!/usr/bin/env python3
"""
infrastructure/repositories/triage_log_repository.py テスト
=============================================================

JsonTriageLogRepository の I/O 動作検証。

検証ポイント:
- append: 日次ファイル _triage_log_YYYYMMDD.json への追記
- 既存ファイルへの追記時、既存内容を保持
- load_for_date: 該当日のログを返す
- 同日複数回 append の冪等性（ファイルが累積）
- 日付ファイルが存在しない場合 load_for_date は空リスト
"""

import json

import pytest

from domain.types.triage import TriageDecision, TriageLogEntry
from infrastructure.repositories.triage_log_repository import (
    JsonTriageLogRepository,
)

# =============================================================================
# Helpers
# =============================================================================


def make_log_entry(
    timestamp: str = "2026-04-07T14:30:22+09:00",
    entry_id: str = "email_20260407_143022_abc12345",
    primary_shard: str = "projects",
    llm_invoked: bool = False,
) -> TriageLogEntry:
    decision: TriageDecision = {
        "entry_id": entry_id,
        "primary_shard": primary_shard,  # type: ignore[typeddict-item]
        "primary_slug": "X",
        "secondary_tags": [],
        "confidence": "rule_match",
        "matched_rules": ["pattern1"],
    }
    return {
        "timestamp": timestamp,
        "decision": decision,
        "llm_invoked": llm_invoked,
    }


# =============================================================================
# append
# =============================================================================


class TestJsonTriageLogRepositoryAppend:
    @pytest.mark.integration
    def test_append_creates_file(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        repo = JsonTriageLogRepository(triage_logs_dir=tmp_path)
        entry = make_log_entry()
        repo.append(entry)
        files = list(tmp_path.glob("_triage_log_*.json"))
        assert len(files) == 1
        assert files[0].name == "_triage_log_20260407.json"

    @pytest.mark.integration
    def test_append_writes_json_array(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        repo = JsonTriageLogRepository(triage_logs_dir=tmp_path)
        repo.append(make_log_entry())
        f = tmp_path / "_triage_log_20260407.json"
        data = json.loads(f.read_text(encoding="utf-8"))
        assert isinstance(data, list)
        assert len(data) == 1

    @pytest.mark.integration
    def test_append_creates_dir_if_missing(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        nested = tmp_path / "a" / "b" / "logs"
        repo = JsonTriageLogRepository(triage_logs_dir=nested)
        repo.append(make_log_entry())
        assert nested.exists()

    @pytest.mark.integration
    def test_append_preserves_existing(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        """既存ログを失わずに追記"""
        repo = JsonTriageLogRepository(triage_logs_dir=tmp_path)
        first = make_log_entry(entry_id="email_20260407_140000_aaaaaaaa")
        second = make_log_entry(entry_id="email_20260407_150000_bbbbbbbb")
        repo.append(first)
        repo.append(second)
        f = tmp_path / "_triage_log_20260407.json"
        data = json.loads(f.read_text(encoding="utf-8"))
        ids = [e["decision"]["entry_id"] for e in data]
        assert ids == [
            "email_20260407_140000_aaaaaaaa",
            "email_20260407_150000_bbbbbbbb",
        ]

    @pytest.mark.integration
    def test_different_days_create_separate_files(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        repo = JsonTriageLogRepository(triage_logs_dir=tmp_path)
        repo.append(make_log_entry(timestamp="2026-04-07T14:30:22+09:00"))
        repo.append(make_log_entry(timestamp="2026-04-08T10:00:00+09:00"))
        files = sorted(p.name for p in tmp_path.glob("_triage_log_*.json"))
        assert files == [
            "_triage_log_20260407.json",
            "_triage_log_20260408.json",
        ]


# =============================================================================
# load_for_date
# =============================================================================


class TestJsonTriageLogRepositoryLoad:
    @pytest.mark.integration
    def test_load_empty_when_no_file(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        repo = JsonTriageLogRepository(triage_logs_dir=tmp_path)
        assert repo.load_for_date("2026-04-07") == []

    @pytest.mark.integration
    def test_load_returns_appended_entries(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        repo = JsonTriageLogRepository(triage_logs_dir=tmp_path)
        repo.append(make_log_entry(entry_id="email_20260407_143022_aaaaaaaa"))
        repo.append(make_log_entry(entry_id="email_20260407_143023_bbbbbbbb"))
        loaded = repo.load_for_date("2026-04-07")
        assert len(loaded) == 2
        assert loaded[0]["decision"]["entry_id"] == "email_20260407_143022_aaaaaaaa"

    @pytest.mark.integration
    def test_load_iso_date_format(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        """date 引数は YYYY-MM-DD でも YYYYMMDD でも受け付ける"""
        repo = JsonTriageLogRepository(triage_logs_dir=tmp_path)
        repo.append(make_log_entry())
        a = repo.load_for_date("2026-04-07")
        b = repo.load_for_date("20260407")
        assert len(a) == len(b) == 1


# =============================================================================
# 日付パース失敗
# =============================================================================


class TestJsonTriageLogRepositoryDateParse:
    @pytest.mark.integration
    def test_invalid_timestamp_raises(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        from domain.exceptions import TriageError

        repo = JsonTriageLogRepository(triage_logs_dir=tmp_path)
        bad = make_log_entry(timestamp="not-a-timestamp")
        with pytest.raises(TriageError):
            repo.append(bad)

#!/usr/bin/env python3
"""
application/status/metrics_collector.py テスト
================================================

MetricsCollectorUseCase の動作検証。

検証ポイント:
- raw_entries_count: inbox/raw-entries/ のエントリ数
- alias_records_total / active / archived: alias resolver の集計
- alias_per_shard: シャード別カウント
- triage_unclassified_pending: inbox/unclassified/ のエントリ数（あれば）
- 不存在ディレクトリ → 0（フェイル不可）
"""

from typing import List

import pytest

from application.status.metrics_collector import MetricsCollectorUseCase, StatusMetrics
from test.test_helpers import (
    FakeAliasResolverRepository,
    FakeEntryRepository,
    build_alias_record,
    build_raw_entry,
)

# =============================================================================
# Helpers
# =============================================================================


def _make_uc(
    raw_entries=None,
    alias_records=None,
    unclassified_count=0,
):  # type: ignore[no-untyped-def]
    entry_repo = FakeEntryRepository()
    for e in raw_entries or []:
        entry_repo.save(e)
    alias_repo = FakeAliasResolverRepository(initial=alias_records or [])
    return MetricsCollectorUseCase(
        entry_repository=entry_repo,
        alias_repository=alias_repo,
        unclassified_count_provider=lambda: unclassified_count,
    )


# =============================================================================
# 基本動作
# =============================================================================


class TestMetricsCollectorBasic:
    @pytest.mark.unit
    def test_returns_status_metrics(self) -> None:
        uc = _make_uc()
        result = uc.execute()
        assert isinstance(result, StatusMetrics)

    @pytest.mark.unit
    def test_empty_state(self) -> None:
        uc = _make_uc()
        result = uc.execute()
        assert result.raw_entries_count == 0
        assert result.alias_records_total == 0
        assert result.alias_records_active == 0
        assert result.alias_records_archived == 0
        assert result.unclassified_count == 0

    @pytest.mark.unit
    def test_counts_raw_entries(self) -> None:
        entries = [build_raw_entry(entry_id=f"email_20260407_14302{i}_aaaaaaaa") for i in range(3)]
        uc = _make_uc(raw_entries=entries)
        result = uc.execute()
        assert result.raw_entries_count == 3

    @pytest.mark.unit
    def test_counts_alias_records(self) -> None:
        records = [
            build_alias_record(slug="A", archive_status="active"),
            build_alias_record(slug="B", archive_status="active"),
            build_alias_record(slug="C", archive_status="removed"),
        ]
        uc = _make_uc(alias_records=records)
        result = uc.execute()
        assert result.alias_records_total == 3
        assert result.alias_records_active == 2
        assert result.alias_records_removed == 1
        assert result.alias_records_archived == 1

    @pytest.mark.unit
    def test_counts_completed_and_removed_separately(self) -> None:
        records = [
            build_alias_record(slug="A", archive_status="active"),
            build_alias_record(
                slug="B",
                archive_status="completed",
                target_path="archive/projects/B/_project.md",
            ),
            build_alias_record(slug="C", archive_status="removed"),
            build_alias_record(
                slug="D",
                archive_status="completed",
                target_path="archive/projects/D/_project.md",
            ),
        ]
        uc = _make_uc(alias_records=records)
        result = uc.execute()
        assert result.alias_records_active == 1
        assert result.alias_records_completed == 2
        assert result.alias_records_removed == 1
        assert result.alias_records_archived == 3  # completed + removed

    @pytest.mark.unit
    def test_alias_per_shard(self) -> None:
        records = [
            build_alias_record(kind="projects", slug="P1"),
            build_alias_record(kind="projects", slug="P2"),
            build_alias_record(kind="clients", slug="C1"),
            build_alias_record(kind="vendors", slug="V1"),
            build_alias_record(kind="knowledge", slug="K1"),
        ]
        uc = _make_uc(alias_records=records)
        result = uc.execute()
        assert result.alias_per_shard["projects"] == 2
        assert result.alias_per_shard["clients"] == 1
        assert result.alias_per_shard["vendors"] == 1
        assert result.alias_per_shard["knowledge"] == 1

    @pytest.mark.unit
    def test_alias_per_shard_excludes_non_active_from_active_count(self) -> None:
        records = [
            build_alias_record(kind="projects", slug="P1", archive_status="active"),
            build_alias_record(kind="projects", slug="P2", archive_status="removed"),
            build_alias_record(
                kind="projects",
                slug="P3",
                archive_status="completed",
                target_path="archive/projects/P3/_project.md",
            ),
        ]
        uc = _make_uc(alias_records=records)
        result = uc.execute()
        # alias_per_shard はアクティブのみカウント
        assert result.alias_per_shard["projects"] == 1

    @pytest.mark.unit
    def test_unclassified_count(self) -> None:
        uc = _make_uc(unclassified_count=5)
        result = uc.execute()
        assert result.unclassified_count == 5


# =============================================================================
# StatusMetrics
# =============================================================================


class TestStatusMetrics:
    @pytest.mark.unit
    def test_to_dict(self) -> None:
        metrics = StatusMetrics(
            raw_entries_count=10,
            alias_records_total=5,
            alias_records_active=4,
            alias_records_archived=1,
            alias_per_shard={"projects": 2, "clients": 1, "vendors": 1, "knowledge": 0},
            unclassified_count=3,
        )
        d = metrics.to_dict()
        assert d["raw_entries_count"] == 10
        assert d["alias_records_total"] == 5
        assert d["alias_per_shard"]["projects"] == 2
        assert d["unclassified_count"] == 3

#!/usr/bin/env python3
"""
application/archive/archive_orchestrator.py テスト
====================================================

ArchiveOrchestrator の動作検証。

責務（業務計画書 §3.3 アーカイブフェーズ）:
- create_manifest: 案件 slug → ArchiveManifest を構築
- execute: ファイル移動指示 + resolver 更新（manifest を返す、実際の I/O は infrastructure 任せ）

設計:
- アーカイブ対話 (AskUserQuestion) は md スキル側
- Python は manifest 構築 + 移動指示のみ
- 実ファイル移動は CLI 側で行うため、ArchiveOrchestrator は manifest 生成と
  resolver 更新のみを行う
"""

from datetime import datetime, timezone

import pytest

from application.archive.archive_orchestrator import ArchiveOrchestrator
from application.resolver.resolver_service import ResolverService
from domain.exceptions import EntityNotFoundError
from test.test_helpers import (
    FakeAliasResolverRepository,
    FakeClock,
    build_alias_record,
)

# =============================================================================
# Helpers
# =============================================================================


def _make_orchestrator(initial_records=None, fixed_time=None):  # type: ignore[no-untyped-def]
    repo = FakeAliasResolverRepository(initial=initial_records or [])
    svc = ResolverService(repo)
    clock = FakeClock(fixed=fixed_time or datetime(2026, 4, 7, 15, 0, 0, tzinfo=timezone.utc))
    return ArchiveOrchestrator(resolver_service=svc, clock=clock), repo


# =============================================================================
# create_manifest
# =============================================================================


class TestArchiveOrchestratorCreateManifest:
    @pytest.mark.unit
    def test_creates_manifest_for_existing_project(self) -> None:
        records = [
            build_alias_record(
                kind="projects",
                slug="MaruMaru",
                canonical="○○マンション",
                target_path="shards/projects/MaruMaru/_project.md",
            )
        ]
        orch, _ = _make_orchestrator(initial_records=records)
        manifest = orch.create_manifest("MaruMaru", reason="完工")

        assert manifest["project_slug"] == "MaruMaru"
        assert manifest["project_canonical"] == "○○マンション"
        assert manifest["reason"] == "完工"
        assert manifest["source_path"] == "shards/projects/MaruMaru"
        assert manifest["destination_path"] == "archive/projects/MaruMaru"
        assert manifest["extracted_knowledge"] == []

    @pytest.mark.unit
    def test_archived_at_uses_clock(self) -> None:
        records = [build_alias_record(slug="X")]
        fixed = datetime(2026, 5, 1, 12, 0, 0, tzinfo=timezone.utc)
        orch, _ = _make_orchestrator(initial_records=records, fixed_time=fixed)
        manifest = orch.create_manifest("X")
        assert manifest["archived_at"].startswith("2026-05-01")

    @pytest.mark.unit
    def test_unknown_project_raises(self) -> None:
        orch, _ = _make_orchestrator(initial_records=[])
        with pytest.raises(EntityNotFoundError):
            orch.create_manifest("Unknown")

    @pytest.mark.unit
    def test_only_projects_can_be_archived(self) -> None:
        records = [build_alias_record(kind="clients", slug="C1")]
        orch, _ = _make_orchestrator(initial_records=records)
        with pytest.raises(EntityNotFoundError):
            orch.create_manifest("C1")

    @pytest.mark.unit
    def test_already_archived_project_raises(self) -> None:
        records = [build_alias_record(slug="Done", archived=True)]
        orch, _ = _make_orchestrator(initial_records=records)
        from domain.exceptions import ArchiveError

        with pytest.raises(ArchiveError, match="already archived"):
            orch.create_manifest("Done")

    @pytest.mark.unit
    def test_default_reason_is_completed(self) -> None:
        records = [build_alias_record(slug="X")]
        orch, _ = _make_orchestrator(initial_records=records)
        manifest = orch.create_manifest("X")
        assert manifest["reason"] == "completed"


# =============================================================================
# execute
# =============================================================================


class TestArchiveOrchestratorExecute:
    @pytest.mark.unit
    def test_execute_marks_resolver_archived(self) -> None:
        records = [
            build_alias_record(
                slug="MaruMaru",
                target_path="shards/projects/MaruMaru/_project.md",
            )
        ]
        orch, repo = _make_orchestrator(initial_records=records)
        manifest = orch.execute("MaruMaru", reason="完工")
        # resolver で archived = True に更新
        loaded = repo.load_all()[0]
        assert loaded["archived"] is True
        # target_path も archive/ に更新
        assert "archive/projects/MaruMaru" in loaded["target_path"]
        # manifest 返却
        assert manifest["project_slug"] == "MaruMaru"

    @pytest.mark.unit
    def test_execute_idempotent_after_first_call(self) -> None:
        """1回目で archived=True、2回目は ArchiveError"""
        records = [build_alias_record(slug="X")]
        orch, _ = _make_orchestrator(initial_records=records)
        orch.execute("X")
        from domain.exceptions import ArchiveError

        with pytest.raises(ArchiveError, match="already archived"):
            orch.execute("X")

#!/usr/bin/env python3
"""
infrastructure/repositories/alias_resolver_repository.py テスト
=================================================================

MarkdownAliasResolverRepository の I/O 動作検証。

検証ポイント:
- 業務計画書 §4.3 のフォーマットに準拠した md を生成
- save_all → load_all のラウンドトリップで内容一致
- 4 シャードのセクション分けが維持される
- v4: archive_status 3 状態 (active/completed/removed) × 4 kind で最大 16 セクション
- completed → `## archive/<kind>/ [completed]`
- removed → `## archive/<kind>/ [removed]`
- aliases (also: ...) を正しくシリアライズ/デシリアライズ
"""

import pytest

from infrastructure.repositories.alias_resolver_repository import (
    MarkdownAliasResolverRepository,
)
from test.test_helpers import build_alias_record

# =============================================================================
# save_all
# =============================================================================


class TestMarkdownAliasResolverRepositorySaveAll:
    @pytest.mark.integration
    def test_save_all_creates_file(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        path = tmp_path / "_alias_resolver.md"
        repo = MarkdownAliasResolverRepository(file_path=path)
        repo.save_all([build_alias_record(slug="A")])
        assert path.exists()

    @pytest.mark.integration
    def test_save_all_writes_global_index_header(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        path = tmp_path / "_alias_resolver.md"
        repo = MarkdownAliasResolverRepository(file_path=path)
        repo.save_all([])
        content = path.read_text(encoding="utf-8")
        assert "# Global Index" in content

    @pytest.mark.integration
    def test_save_all_creates_section_per_shard(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        path = tmp_path / "_alias_resolver.md"
        repo = MarkdownAliasResolverRepository(file_path=path)
        repo.save_all(
            [
                build_alias_record(kind="projects", slug="P"),
                build_alias_record(kind="clients", slug="C"),
                build_alias_record(kind="vendors", slug="V"),
                build_alias_record(kind="knowledge", slug="K"),
            ]
        )
        content = path.read_text(encoding="utf-8")
        assert "## projects/" in content
        assert "## clients/" in content
        assert "## vendors/" in content
        assert "## knowledge/" in content

    @pytest.mark.integration
    def test_save_all_writes_aliases_inline(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        path = tmp_path / "_alias_resolver.md"
        repo = MarkdownAliasResolverRepository(file_path=path)
        repo.save_all(
            [
                build_alias_record(
                    slug="MaruMaru",
                    canonical="○○マンション",
                    aliases=["○○MS", "現場番号2026-003"],
                )
            ]
        )
        content = path.read_text(encoding="utf-8")
        assert "○○マンション" in content
        assert "also:" in content
        assert "○○MS" in content
        assert "現場番号2026-003" in content

    @pytest.mark.integration
    def test_save_all_removed_in_archive_removed_section(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        path = tmp_path / "_alias_resolver.md"
        repo = MarkdownAliasResolverRepository(file_path=path)
        repo.save_all(
            [
                build_alias_record(slug="Active", archive_status="active"),
                build_alias_record(slug="Gone", archive_status="removed"),
            ]
        )
        content = path.read_text(encoding="utf-8")
        assert "## archive/projects/ [removed]" in content

    @pytest.mark.integration
    def test_save_all_completed_in_archive_completed_section(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        path = tmp_path / "_alias_resolver.md"
        repo = MarkdownAliasResolverRepository(file_path=path)
        repo.save_all(
            [
                build_alias_record(slug="Active", archive_status="active"),
                build_alias_record(
                    slug="Done",
                    archive_status="completed",
                    target_path="archive/projects/Done/_project.md",
                ),
            ]
        )
        content = path.read_text(encoding="utf-8")
        assert "## archive/projects/ [completed]" in content

    @pytest.mark.integration
    def test_save_all_mixed_3_statuses(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        """3 状態混在時も全セクションが正しく出力される"""
        path = tmp_path / "_alias_resolver.md"
        repo = MarkdownAliasResolverRepository(file_path=path)
        repo.save_all(
            [
                build_alias_record(slug="A", archive_status="active"),
                build_alias_record(
                    slug="B",
                    archive_status="completed",
                    target_path="archive/projects/B/_project.md",
                ),
                build_alias_record(slug="C", archive_status="removed"),
            ]
        )
        content = path.read_text(encoding="utf-8")
        assert "## projects/" in content
        assert "## archive/projects/ [completed]" in content
        assert "## archive/projects/ [removed]" in content

    @pytest.mark.integration
    def test_save_all_creates_dir_if_missing(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        path = tmp_path / "deep" / "nest" / "_alias_resolver.md"
        repo = MarkdownAliasResolverRepository(file_path=path)
        repo.save_all([])
        assert path.exists()


# =============================================================================
# load_all
# =============================================================================


class TestMarkdownAliasResolverRepositoryLoadAll:
    @pytest.mark.integration
    def test_load_all_empty_file(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        path = tmp_path / "_alias_resolver.md"
        repo = MarkdownAliasResolverRepository(file_path=path)
        repo.save_all([])
        result = repo.load_all()
        assert result == []

    @pytest.mark.integration
    def test_load_all_when_file_missing(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        """ファイル不存在は空リスト（初回起動の通常状態）"""
        path = tmp_path / "_alias_resolver.md"
        repo = MarkdownAliasResolverRepository(file_path=path)
        assert repo.load_all() == []

    @pytest.mark.integration
    def test_round_trip_single_record(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        path = tmp_path / "_alias_resolver.md"
        repo = MarkdownAliasResolverRepository(file_path=path)
        original = [
            build_alias_record(
                slug="MaruMaru",
                canonical="○○マンション",
                aliases=["○○MS", "現場番号2026-003"],
            )
        ]
        repo.save_all(original)
        loaded = repo.load_all()
        assert len(loaded) == 1
        assert loaded[0]["id"] == "projects/MaruMaru"
        assert loaded[0]["canonical"] == "○○マンション"
        assert sorted(loaded[0]["aliases"]) == sorted(["○○MS", "現場番号2026-003"])
        assert loaded[0]["archive_status"] == "active"

    @pytest.mark.integration
    def test_round_trip_all_shards(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        path = tmp_path / "_alias_resolver.md"
        repo = MarkdownAliasResolverRepository(file_path=path)
        original = [
            build_alias_record(kind="projects", slug="P"),
            build_alias_record(kind="clients", slug="C"),
            build_alias_record(kind="vendors", slug="V"),
            build_alias_record(kind="knowledge", slug="K"),
        ]
        repo.save_all(original)
        loaded = repo.load_all()
        assert len(loaded) == 4
        kinds = sorted(r["shard"] for r in loaded)
        assert kinds == ["clients", "knowledge", "projects", "vendors"]

    @pytest.mark.integration
    def test_round_trip_with_removed(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        path = tmp_path / "_alias_resolver.md"
        repo = MarkdownAliasResolverRepository(file_path=path)
        original = [
            build_alias_record(slug="Active", archive_status="active"),
            build_alias_record(slug="Gone", archive_status="removed"),
        ]
        repo.save_all(original)
        loaded = repo.load_all()
        status_map = {r["id"]: r["archive_status"] for r in loaded}
        assert status_map["projects/Active"] == "active"
        assert status_map["projects/Gone"] == "removed"

    @pytest.mark.integration
    def test_round_trip_with_completed(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        path = tmp_path / "_alias_resolver.md"
        repo = MarkdownAliasResolverRepository(file_path=path)
        original = [
            build_alias_record(slug="Active", archive_status="active"),
            build_alias_record(
                slug="Done",
                archive_status="completed",
                target_path="archive/projects/Done/_project.md",
            ),
        ]
        repo.save_all(original)
        loaded = repo.load_all()
        status_map = {r["id"]: r["archive_status"] for r in loaded}
        assert status_map["projects/Active"] == "active"
        assert status_map["projects/Done"] == "completed"
        # target_path も保持
        path_map = {r["id"]: r["target_path"] for r in loaded}
        assert path_map["projects/Done"] == "archive/projects/Done/_project.md"

    @pytest.mark.integration
    def test_round_trip_3_statuses_preserves_all(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        """3 状態混在のラウンドトリップで status, target_path, aliases 全てが保持される"""
        path = tmp_path / "_alias_resolver.md"
        repo = MarkdownAliasResolverRepository(file_path=path)
        original = [
            build_alias_record(slug="Live", archive_status="active"),
            build_alias_record(
                slug="Finished",
                archive_status="completed",
                target_path="archive/projects/Finished/_project.md",
                aliases=["完工", "終了案件"],
            ),
            build_alias_record(
                slug="Dropped",
                archive_status="removed",
                aliases=["誤登録"],
            ),
        ]
        repo.save_all(original)
        loaded = repo.load_all()
        assert len(loaded) == 3
        by_id = {r["id"]: r for r in loaded}
        assert by_id["projects/Live"]["archive_status"] == "active"
        assert by_id["projects/Finished"]["archive_status"] == "completed"
        assert by_id["projects/Dropped"]["archive_status"] == "removed"
        assert sorted(by_id["projects/Finished"]["aliases"]) == ["完工", "終了案件"]
        assert sorted(by_id["projects/Dropped"]["aliases"]) == ["誤登録"]

    @pytest.mark.integration
    def test_round_trip_no_aliases(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        path = tmp_path / "_alias_resolver.md"
        repo = MarkdownAliasResolverRepository(file_path=path)
        original = [build_alias_record(slug="X", aliases=[])]
        repo.save_all(original)
        loaded = repo.load_all()
        assert loaded[0]["aliases"] == []

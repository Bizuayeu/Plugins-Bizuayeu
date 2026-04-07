#!/usr/bin/env python3
"""
infrastructure/repositories/alias_resolver_repository.py テスト
=================================================================

MarkdownAliasResolverRepository の I/O 動作検証。

検証ポイント:
- 業務計画書 §4.3 のフォーマットに準拠した md を生成
- save_all → load_all のラウンドトリップで内容一致
- 4 シャードのセクション分けが維持される
- archive (archived=True) は archive/ セクションに振り分け
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
    def test_save_all_archived_in_archive_section(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        path = tmp_path / "_alias_resolver.md"
        repo = MarkdownAliasResolverRepository(file_path=path)
        repo.save_all(
            [
                build_alias_record(slug="Active", archived=False),
                build_alias_record(slug="Archived", archived=True),
            ]
        )
        content = path.read_text(encoding="utf-8")
        assert "## archive/" in content

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
        assert loaded[0]["archived"] is False

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
    def test_round_trip_with_archived(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        path = tmp_path / "_alias_resolver.md"
        repo = MarkdownAliasResolverRepository(file_path=path)
        original = [
            build_alias_record(slug="Active", archived=False),
            build_alias_record(slug="Done", archived=True),
        ]
        repo.save_all(original)
        loaded = repo.load_all()
        archived_map = {r["id"]: r["archived"] for r in loaded}
        assert archived_map["projects/Active"] is False
        assert archived_map["projects/Done"] is True

    @pytest.mark.integration
    def test_round_trip_no_aliases(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        path = tmp_path / "_alias_resolver.md"
        repo = MarkdownAliasResolverRepository(file_path=path)
        original = [build_alias_record(slug="X", aliases=[])]
        repo.save_all(original)
        loaded = repo.load_all()
        assert loaded[0]["aliases"] == []

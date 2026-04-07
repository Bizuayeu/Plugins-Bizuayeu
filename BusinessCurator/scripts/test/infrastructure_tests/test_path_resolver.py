#!/usr/bin/env python3
"""
infrastructure/path_resolver.py テスト
======================================

PathResolver の plugin_root 解決ロジック検証。

設計意図:
- plugin_root は `_root.md` または `_alias_resolver.md` を含むディレクトリ
- カレントディレクトリ ↑ に向かって探索
- 見つからなければ FileNotFoundError
- 一度解決したパスから shards/ inbox/ archive/ triage_logs/ を導出可能
"""

import pytest

from infrastructure.path_resolver import PathResolver

# =============================================================================
# 探索
# =============================================================================


class TestPathResolverFind:
    @pytest.mark.integration
    def test_finds_root_when_marker_in_current_dir(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        """カレントに _root.md があれば即発見"""
        (tmp_path / "_root.md").write_text("# root")
        result = PathResolver.find_plugin_root(tmp_path)
        assert result == tmp_path

    @pytest.mark.integration
    def test_finds_root_when_marker_in_parent(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        """親ディレクトリに _root.md があっても発見"""
        (tmp_path / "_root.md").write_text("# root")
        nested = tmp_path / "a" / "b" / "c"
        nested.mkdir(parents=True)
        result = PathResolver.find_plugin_root(nested)
        assert result == tmp_path

    @pytest.mark.integration
    def test_finds_via_alias_resolver_marker(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        """_alias_resolver.md のみでも発見"""
        (tmp_path / "_alias_resolver.md").write_text("# resolver")
        result = PathResolver.find_plugin_root(tmp_path)
        assert result == tmp_path

    @pytest.mark.integration
    def test_raises_when_no_marker_found(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        """マーカーがどこにもなければ FileNotFoundError"""
        with pytest.raises(FileNotFoundError, match="plugin_root"):
            PathResolver.find_plugin_root(tmp_path)


# =============================================================================
# 派生パス
# =============================================================================


class TestPathResolverDerivedPaths:
    """plugin_root から各種ディレクトリパスを導出"""

    @pytest.fixture
    def resolver(self, tmp_path):  # type: ignore[no-untyped-def]
        (tmp_path / "_root.md").write_text("# root")
        return PathResolver(tmp_path)

    @pytest.mark.unit
    def test_inbox_dir(self, resolver: PathResolver) -> None:
        assert resolver.inbox_dir.name == "inbox"
        assert resolver.inbox_dir.parent == resolver.plugin_root

    @pytest.mark.unit
    def test_raw_entries_dir(self, resolver: PathResolver) -> None:
        assert resolver.raw_entries_dir.name == "raw-entries"
        assert resolver.raw_entries_dir.parent == resolver.inbox_dir

    @pytest.mark.unit
    def test_unclassified_dir(self, resolver: PathResolver) -> None:
        assert resolver.unclassified_dir.name == "unclassified"
        assert resolver.unclassified_dir.parent == resolver.inbox_dir

    @pytest.mark.unit
    def test_shards_dir(self, resolver: PathResolver) -> None:
        assert resolver.shards_dir.name == "shards"

    @pytest.mark.unit
    def test_archive_dir(self, resolver: PathResolver) -> None:
        assert resolver.archive_dir.name == "archive"

    @pytest.mark.unit
    def test_triage_logs_dir(self, resolver: PathResolver) -> None:
        assert resolver.triage_logs_dir.name == "triage_logs"

    @pytest.mark.unit
    def test_alias_resolver_path(self, resolver: PathResolver) -> None:
        assert resolver.alias_resolver_path.name == "_alias_resolver.md"

    @pytest.mark.unit
    def test_root_wiki_path(self, resolver: PathResolver) -> None:
        assert resolver.root_wiki_path.name == "_root.md"

    @pytest.mark.unit
    def test_shard_dir_for_kind(self, resolver: PathResolver) -> None:
        """shard_dir('projects') → shards/projects/"""
        d = resolver.shard_dir("projects")
        assert d.parent == resolver.shards_dir
        assert d.name == "projects"

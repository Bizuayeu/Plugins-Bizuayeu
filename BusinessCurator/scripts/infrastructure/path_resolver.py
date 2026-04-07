#!/usr/bin/env python3
"""
PathResolver
============

plugin_root の探索と派生パスの導出。

設計意図:
- BusinessCurator は config 層を持たない（業務計画書の3点改変1.3）
- plugin_root マーカーは `_root.md` または `_alias_resolver.md`
- カレントディレクトリから ↑ に向かって探索
- 見つかった root から inbox/ shards/ archive/ triage_logs/ を導出

Usage:
    from infrastructure.path_resolver import PathResolver
    resolver = PathResolver(PathResolver.find_plugin_root())
    print(resolver.inbox_dir)
"""

from pathlib import Path

from domain.constants import (
    ALIAS_RESOLVER_FILENAME,
    ARCHIVE_DIR_NAME,
    INBOX_DIR_NAME,
    RAW_ENTRIES_DIR_NAME,
    ROOT_WIKI_FILENAME,
    SHARDS_DIR_NAME,
    TRIAGE_LOGS_DIR_NAME,
    UNCLASSIFIED_DIR_NAME,
)
from domain.types.shard import ShardKind

__all__ = ["PathResolver"]


# マーカーファイル候補（先頭を優先）
_PLUGIN_ROOT_MARKERS = (ROOT_WIKI_FILENAME, ALIAS_RESOLVER_FILENAME)


class PathResolver:
    """
    plugin_root を起点に派生パスを返すヘルパー
    """

    def __init__(self, plugin_root: Path) -> None:
        self._root = plugin_root.resolve()

    # ------------------------------------------------------------------
    # static: 探索
    # ------------------------------------------------------------------

    @staticmethod
    def find_plugin_root(start: Path) -> Path:
        """
        start から ↑ に向かって plugin_root マーカーを探索

        Args:
            start: 探索開始ディレクトリ

        Returns:
            plugin_root として検出されたディレクトリ

        Raises:
            FileNotFoundError: マーカーが見つからない
        """
        current = start.resolve()
        candidates = [current, *current.parents]
        for d in candidates:
            for marker in _PLUGIN_ROOT_MARKERS:
                if (d / marker).is_file():
                    return d
        raise FileNotFoundError(
            f"plugin_root not found above {start} (looked for {_PLUGIN_ROOT_MARKERS})"
        )

    # ------------------------------------------------------------------
    # 基本パス
    # ------------------------------------------------------------------

    @property
    def plugin_root(self) -> Path:
        return self._root

    @property
    def inbox_dir(self) -> Path:
        return self._root / INBOX_DIR_NAME

    @property
    def raw_entries_dir(self) -> Path:
        return self.inbox_dir / RAW_ENTRIES_DIR_NAME

    @property
    def unclassified_dir(self) -> Path:
        return self.inbox_dir / UNCLASSIFIED_DIR_NAME

    @property
    def shards_dir(self) -> Path:
        return self._root / SHARDS_DIR_NAME

    @property
    def archive_dir(self) -> Path:
        return self._root / ARCHIVE_DIR_NAME

    @property
    def triage_logs_dir(self) -> Path:
        return self._root / TRIAGE_LOGS_DIR_NAME

    @property
    def alias_resolver_path(self) -> Path:
        return self._root / ALIAS_RESOLVER_FILENAME

    @property
    def root_wiki_path(self) -> Path:
        return self._root / ROOT_WIKI_FILENAME

    def shard_dir(self, kind: ShardKind) -> Path:
        """シャード種別ごとのディレクトリ（shards/{kind}/）"""
        return self.shards_dir / kind

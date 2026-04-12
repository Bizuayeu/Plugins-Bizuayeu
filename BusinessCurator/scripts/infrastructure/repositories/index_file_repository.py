#!/usr/bin/env python3
"""
IndexFileRepository
===================

`_index.md` ツリー（ルート + 各シャード）のファイル永続化。

設計意図:
- 純粋な I/O のみ。Markdown 整形は interfaces 層の責務。
- 親ディレクトリの自動作成（shards/{kind}/ が未作成の環境でも安全）
- 既存ファイルは問答無用で上書き（冪等な再生成のため）
"""

from pathlib import Path

from domain.constants import SHARDS_DIR_NAME
from domain.types.shard import ShardKind

__all__ = ["IndexFileRepository"]

_INDEX_FILENAME = "_index.md"


class IndexFileRepository:
    """
    `{plugin_root}/_index.md` と `{plugin_root}/shards/{kind}/_index.md` の
    読み書きを担う永続化アダプタ。
    """

    def __init__(self, plugin_root: Path) -> None:
        self._plugin_root = Path(plugin_root)

    def save_root_index(self, content: str) -> None:
        """ルート `_index.md` を書き込む（既存ファイルは上書き）"""
        path = self._plugin_root / _INDEX_FILENAME
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def save_shard_index(self, kind: ShardKind, content: str) -> None:
        """
        シャード別 `_index.md` を書き込む

        親ディレクトリ (`shards/{kind}/`) が無ければ自動作成する。
        """
        shard_dir = self._plugin_root / SHARDS_DIR_NAME / kind
        shard_dir.mkdir(parents=True, exist_ok=True)
        (shard_dir / _INDEX_FILENAME).write_text(content, encoding="utf-8")

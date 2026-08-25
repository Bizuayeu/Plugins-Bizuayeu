#!/usr/bin/env python3
"""
IndexGeneratorService
=====================

`_index.md` ツリー（ルート + 4シャード）の再生成を統括するユースケース。

設計意図:
- ResolverService から取得した AliasRecord を IndexEntry に変換 → domain の
  `group_by_shard` でグルーピング → Formatter で Markdown 化 → Repository で永続化。
- Formatter と Repository は構造型（duck typing）で受け入れる。
  注入する実体は interfaces/formatters および infrastructure/repositories に配置。
- 戻り値は `{shard: count}` の dict（呼び出し側のログ・JSON 出力用）。
"""

from typing import Protocol

from application.resolver.resolver_service import ResolverService
from domain.indexing.index_entry import IndexEntry
from domain.indexing.shard_grouper import group_by_shard
from domain.types.alias import AliasRecord
from domain.types.shard import SHARD_KINDS, ShardKind

__all__ = ["IndexGeneratorService"]


class _FormatterProtocol(Protocol):
    def format_root(self, grouped: dict[str, list[IndexEntry]]) -> str: ...
    def format_shard(self, kind: ShardKind, entries: list[IndexEntry]) -> str: ...


class _FileRepoProtocol(Protocol):
    def save_root_index(self, content: str) -> None: ...
    def save_shard_index(self, kind: ShardKind, content: str) -> None: ...


class IndexGeneratorService:
    """
    `_index.md` ツリーを生成するユースケース

    Dependencies:
        resolver_service: AliasRecord の読み取り元
        file_repo: `_index.md` の書き込み先
        formatter: Markdown 整形器
    """

    def __init__(
        self,
        resolver_service: ResolverService,
        file_repo: _FileRepoProtocol,
        formatter: _FormatterProtocol,
    ) -> None:
        self._resolver = resolver_service
        self._file_repo = file_repo
        self._formatter = formatter

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------

    def regenerate_all(self, include_archived: bool = False) -> dict[str, int]:
        """
        ルート + 全シャードの `_index.md` を再生成する

        Args:
            include_archived: 論理削除レコードを含めるか

        Returns:
            `{shard: entry_count}` の dict。シャードごとの出力件数。
        """
        entries = self._load_entries(include_archived)
        grouped = group_by_shard(entries, include_archived=include_archived)

        counts: dict[str, int] = {}
        for kind in SHARD_KINDS:
            shard_entries = grouped.get(kind, [])
            content = self._formatter.format_shard(kind, shard_entries)
            self._file_repo.save_shard_index(kind, content)
            counts[kind] = len(shard_entries)

        root_content = self._formatter.format_root(grouped)
        self._file_repo.save_root_index(root_content)

        return counts

    def regenerate_shard(self, kind: ShardKind) -> int:
        """
        特定シャードの `_index.md` のみ再生成（ルートは更新しない）

        Args:
            kind: 対象シャード

        Returns:
            出力したエントリ件数
        """
        entries = [e for e in self._load_entries(include_archived=False) if e.shard == kind]
        entries.sort(key=lambda e: e.canonical)
        content = self._formatter.format_shard(kind, entries)
        self._file_repo.save_shard_index(kind, content)
        return len(entries)

    # ------------------------------------------------------------------
    # internal
    # ------------------------------------------------------------------

    def _load_entries(self, include_archived: bool) -> list[IndexEntry]:
        """Resolver から AliasRecord を取得し IndexEntry に変換する"""
        records: list[AliasRecord]
        if include_archived:
            records = list(self._resolver._repo.load_all())  # noqa: SLF001
        else:
            records = self._resolver.list_active()
        return [IndexEntry.from_alias_record(r) for r in records]

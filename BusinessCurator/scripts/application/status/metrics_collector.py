#!/usr/bin/env python3
"""
MetricsCollectorUseCase
=======================

シャード横断のステータスメトリクス集計。

設計意図:
- 業務計画書 §4.2 の「ルートwiki シャード一覧」を支える集計
- 全シャードの活性エンティティ数 / 完工アーカイブ数 / 論理削除数
- raw-entries 件数（ingest 状況）
- inbox/unclassified 件数（triage 残件）
- ファイルシステム依存は callable 経由で注入（unclassified_count_provider）

依存:
- EntryRepositoryProtocol
- AliasResolverRepositoryProtocol
- unclassified_count_provider: () -> int
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from domain.protocols import (
    AliasResolverRepositoryProtocol,
    EntryRepositoryProtocol,
)
from domain.types.shard import SHARD_KINDS

__all__ = ["MetricsCollectorUseCase", "StatusMetrics"]


@dataclass
class StatusMetrics:
    """
    集計結果

    Attributes:
        raw_entries_count: inbox/raw-entries/ のエントリ数
        alias_records_total: alias resolver の総レコード数
        alias_records_active: archive_status == "active" のレコード数
        alias_records_completed: archive_status == "completed" のレコード数
        alias_records_removed: archive_status == "removed" のレコード数
        alias_records_archived: completed + removed の合計（後方表示互換用）
        alias_per_shard: シャード別アクティブカウント
        unclassified_count: inbox/unclassified/ の件数
    """

    raw_entries_count: int = 0
    alias_records_total: int = 0
    alias_records_active: int = 0
    alias_records_completed: int = 0
    alias_records_removed: int = 0
    alias_records_archived: int = 0
    alias_per_shard: dict[str, int] = field(default_factory=dict)
    unclassified_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "raw_entries_count": self.raw_entries_count,
            "alias_records_total": self.alias_records_total,
            "alias_records_active": self.alias_records_active,
            "alias_records_completed": self.alias_records_completed,
            "alias_records_removed": self.alias_records_removed,
            "alias_records_archived": self.alias_records_archived,
            "alias_per_shard": dict(self.alias_per_shard),
            "unclassified_count": self.unclassified_count,
        }


class MetricsCollectorUseCase:
    """シャード横断メトリクス集計"""

    def __init__(
        self,
        entry_repository: EntryRepositoryProtocol,
        alias_repository: AliasResolverRepositoryProtocol,
        unclassified_count_provider: Callable[[], int],
    ) -> None:
        self._entry_repo = entry_repository
        self._alias_repo = alias_repository
        self._unclassified_provider = unclassified_count_provider

    def execute(self) -> StatusMetrics:
        """
        メトリクスを集計

        Returns:
            StatusMetrics
        """
        entries = self._entry_repo.list_all()
        records = self._alias_repo.load_all()

        active_records = [r for r in records if r["archive_status"] == "active"]
        completed_records = [r for r in records if r["archive_status"] == "completed"]
        removed_records = [r for r in records if r["archive_status"] == "removed"]

        per_shard: dict[str, int] = {k: 0 for k in SHARD_KINDS}
        for r in active_records:
            per_shard[r["shard"]] += 1

        return StatusMetrics(
            raw_entries_count=len(entries),
            alias_records_total=len(records),
            alias_records_active=len(active_records),
            alias_records_completed=len(completed_records),
            alias_records_removed=len(removed_records),
            alias_records_archived=len(completed_records) + len(removed_records),
            alias_per_shard=per_shard,
            unclassified_count=self._unclassified_provider(),
        )

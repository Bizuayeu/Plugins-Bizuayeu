#!/usr/bin/env python3
"""
Shard Grouper
=============

IndexEntry のリストをシャードごとにグルーピング & canonical でソートする
純粋ドメインサービス。

設計意図:
- 純粋関数（副作用なし、外部依存なし）
- archive_status の包含/除外はドメインポリシーのためここで実装
- Python の sort は stable なので、同じ canonical のエントリ間は入力順保持
"""

from collections.abc import Iterable

from domain.indexing.index_entry import IndexEntry

__all__ = ["group_by_shard"]


def group_by_shard(
    entries: Iterable[IndexEntry],
    include_archived: bool = False,
) -> dict[str, list[IndexEntry]]:
    """
    IndexEntry をシャード種別ごとにグルーピングし canonical 昇順でソートする

    Args:
        entries: 対象エントリ群
        include_archived: active 以外（completed/removed）も含めるか（既定 False）

    Returns:
        `{shard: [entry, ...], ...}` の辞書。シャードごとに canonical 昇順。
        空入力や全除外の場合は空 dict。
    """
    grouped: dict[str, list[IndexEntry]] = {}
    for entry in entries:
        if entry.archive_status != "active" and not include_archived:
            continue
        grouped.setdefault(entry.shard, []).append(entry)

    for shard_entries in grouped.values():
        shard_entries.sort(key=lambda e: e.canonical)

    return grouped

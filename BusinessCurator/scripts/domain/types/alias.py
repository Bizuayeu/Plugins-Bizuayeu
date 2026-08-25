#!/usr/bin/env python3
"""
Alias Resolver Domain Type
==========================

_alias_resolver.md の1エントリのドメイン表現。

設計意図:
- ResolverService の add/edit/remove/complete_archive/rebuild が扱う単位（業務計画書 §4.3）
- archive_status で 3 状態（active/completed/removed）を単一フィールドで表現
- id は kind/slug 複合キー（"projects/MaruMaruMansion"）

Usage:
    from domain.types.alias import AliasRecord
    from domain.types.shard import ArchiveStatus

    rec: AliasRecord = {
        "id": "projects/MaruMaruMansion",
        "canonical": "○○マンション新築工事",
        "aliases": ["○○MS"],
        "shard": "projects",
        "target_path": "shards/projects/MaruMaruMansion/_project.md",
        "archive_status": "active",
    }
"""

from typing import TypedDict

from domain.types.shard import ArchiveStatus, ShardKind


class AliasRecord(TypedDict):
    """
    エイリアスリゾルバ1エントリ

    Attributes:
        id: 複合キー（"<kind>/<slug>" 形式）
        canonical: 正式名称（md リンクテキスト）
        aliases: also[] のリスト（triage マッチ対象）
        shard: シャード種別
        target_path: リンク先 md パス（plugin_root 相対）
        archive_status: ライフサイクル状態（active/completed/removed）
    """

    id: str
    canonical: str
    aliases: list[str]
    shard: ShardKind
    target_path: str
    archive_status: ArchiveStatus


__all__ = ["AliasRecord"]

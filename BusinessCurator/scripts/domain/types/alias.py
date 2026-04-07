#!/usr/bin/env python3
"""
Alias Resolver Domain Type
==========================

_alias_resolver.md の1エントリのドメイン表現。

設計意図:
- ResolverService の add/edit/remove/rebuild が扱う単位（業務計画書 §4.3）
- archived フラグでアーカイブ後も参照を維持（論理削除）
- id は kind/slug 複合キー（"projects/MaruMaruMansion"）

Usage:
    from domain.types.alias import AliasRecord

    rec: AliasRecord = {
        "id": "projects/MaruMaruMansion",
        "canonical": "○○マンション新築工事",
        ...
    }
"""

from typing import List, TypedDict

from domain.types.shard import ShardKind


class AliasRecord(TypedDict):
    """
    エイリアスリゾルバ1エントリ

    Attributes:
        id: 複合キー（"<kind>/<slug>" 形式）
        canonical: 正式名称（md リンクテキスト）
        aliases: also[] のリスト（triage マッチ対象）
        shard: シャード種別
        target_path: リンク先 md パス（plugin_root 相対）
        archived: アーカイブ済みフラグ
    """

    id: str
    canonical: str
    aliases: List[str]
    shard: ShardKind
    target_path: str
    archived: bool


__all__ = ["AliasRecord"]

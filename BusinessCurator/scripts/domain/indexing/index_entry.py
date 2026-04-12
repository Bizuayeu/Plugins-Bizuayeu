#!/usr/bin/env python3
"""
IndexEntry Value Object
=======================

`_index.md` ツリーが扱う 1 エントリのドメイン表現。

設計意図:
- AliasRecord (TypedDict) は infrastructure/interfaces 層境界の構造型。
  ドメイン内ではより厳密な frozen dataclass を使い、immutability と
  ハッシュ可能性を得る。
- id の分解（"projects/Slug" → slug="Slug"）はここで一元化し、
  application / interfaces 層は slug を直接利用できる。
"""

from dataclasses import dataclass
from typing import Tuple

from domain.types.alias import AliasRecord
from domain.types.shard import ArchiveStatus, ShardKind

__all__ = ["IndexEntry"]


@dataclass(frozen=True)
class IndexEntry:
    """
    `_index.md` の 1 行分のデータ

    Attributes:
        shard: シャード種別
        slug: エンティティ識別子（ASCII）
        canonical: 日本語正式名（リンクテキストになる）
        aliases: 別名（immutable tuple、triage マッチ対象と同じ集合）
        target_path: plugin_root 相対のリンク先パス
        archive_status: ライフサイクル状態（active/completed/removed）
    """

    shard: ShardKind
    slug: str
    canonical: str
    aliases: Tuple[str, ...]
    target_path: str
    archive_status: ArchiveStatus

    @classmethod
    def from_alias_record(cls, record: AliasRecord) -> "IndexEntry":
        """AliasRecord (TypedDict) から IndexEntry を構築"""
        kind, slug = record["id"].split("/", 1)
        return cls(
            shard=record["shard"],
            slug=slug,
            canonical=record["canonical"],
            aliases=tuple(record["aliases"]),
            target_path=record["target_path"],
            archive_status=record["archive_status"],
        )

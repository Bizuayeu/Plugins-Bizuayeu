#!/usr/bin/env python3
"""
Shard Domain Types
==================

シャード種別とエンティティの定義、および archive_status の単一真実源。

設計意図:
- シャードは4種固定（projects/clients/vendors/knowledge）
- 業務計画書 §7.1 「シャードの切り分けは不可逆的行動コストが高い」原則
- Literal型でmypy strict下に静的検出
- ShardEntity は manager 層が登録するマスタデータの中立表現
- ArchiveStatus は v4 で `archived: bool` を置き換えた 3 状態 enum。
  AliasRecord/ShardEntity の両方が同じ定義を参照する（single source of truth）

Usage:
    from domain.types.shard import ShardKind, ShardEntity, SHARD_KINDS
    from domain.types.shard import ArchiveStatus, ARCHIVE_STATUSES

    def is_valid_kind(s: str) -> bool:
        return s in SHARD_KINDS
"""

from typing import Literal, TypedDict

# =============================================================================
# Shard Kind
# =============================================================================

ShardKind = Literal["projects", "clients", "vendors", "knowledge"]
"""4つのシャード種別。業務計画書 §7.1 で固定。"""


SHARD_KINDS: tuple[ShardKind, ...] = ("projects", "clients", "vendors", "knowledge")
"""ShardKind の全値（イテレーション/バリデーション用、immutable）。"""


# =============================================================================
# Archive Status
# =============================================================================

ArchiveStatus = Literal["active", "completed", "removed"]
"""
AliasRecord / ShardEntity のライフサイクル状態。

- active:    通常運用中
- completed: 完工アーカイブ（target_path は archive/<kind>/X 配下）
- removed:   誤登録/取引停止/統合による論理削除（target_path は shards/<kind>/X のまま）
"""


ARCHIVE_STATUSES: tuple[ArchiveStatus, ...] = ("active", "completed", "removed")
"""ArchiveStatus の全値（イテレーション/バリデーション用、immutable）。"""


# =============================================================================
# Shard Entity
# =============================================================================


class ShardEntity(TypedDict):
    """
    シャード内エンティティ（manager 層が登録するマスタデータ）

    Attributes:
        kind: シャード種別
        canonical_name: 正式名称（日本語可）
        slug: ファイル名/ディレクトリ名用 ASCII slug
        aliases: 別名リスト（triage の物件識別子マッチに利用）
        archive_status: ライフサイクル状態（active/completed/removed）
        category: knowledge シャードのカテゴリ（その他は None）
    """

    kind: ShardKind
    canonical_name: str
    slug: str
    aliases: list[str]
    archive_status: ArchiveStatus
    category: str | None


__all__ = [
    "ARCHIVE_STATUSES",
    "ArchiveStatus",
    "SHARD_KINDS",
    "ShardEntity",
    "ShardKind",
]

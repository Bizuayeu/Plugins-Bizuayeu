#!/usr/bin/env python3
"""
Shard Domain Types
==================

シャード種別とエンティティの定義。

設計意図:
- シャードは4種固定（projects/clients/vendors/knowledge）
- 業務計画書 §7.1 「シャードの切り分けは不可逆的行動コストが高い」原則
- Literal型でmypy strict下に静的検出
- ShardEntity は manager 層が登録するマスタデータの中立表現

Usage:
    from domain.types.shard import ShardKind, ShardEntity, SHARD_KINDS

    def is_valid_kind(s: str) -> bool:
        return s in SHARD_KINDS
"""

from typing import List, Literal, Optional, Tuple, TypedDict

# =============================================================================
# Shard Kind
# =============================================================================

ShardKind = Literal["projects", "clients", "vendors", "knowledge"]
"""4つのシャード種別。業務計画書 §7.1 で固定。"""


SHARD_KINDS: Tuple[ShardKind, ...] = ("projects", "clients", "vendors", "knowledge")
"""ShardKind の全値（イテレーション/バリデーション用、immutable）。"""


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
        archived: アーカイブ済みフラグ
        category: knowledge シャードのカテゴリ（その他は None）
    """

    kind: ShardKind
    canonical_name: str
    slug: str
    aliases: List[str]
    archived: bool
    category: Optional[str]


__all__ = ["SHARD_KINDS", "ShardEntity", "ShardKind"]

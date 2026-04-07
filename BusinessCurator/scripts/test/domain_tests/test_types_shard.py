#!/usr/bin/env python3
"""
domain/types/shard.py テスト
============================

ShardKind Literal型とShardEntity TypedDictのテスト。

設計意図:
- シャードは4種固定（projects/clients/vendors/knowledge）
- Literal型でmypy strict下で誤分類を静的検出
- ShardEntity は manager 層が登録するエンティティのドメイン表現
"""

from typing import List, Optional, get_type_hints

import pytest

from domain.types.shard import SHARD_KINDS, ShardEntity, ShardKind

# =============================================================================
# ShardKind Literal
# =============================================================================


class TestShardKind:
    """ShardKind Literal のテスト"""

    @pytest.mark.unit
    def test_projects_is_valid(self) -> None:
        """projects は有効なシャード種別"""
        kind: ShardKind = "projects"
        assert kind == "projects"

    @pytest.mark.unit
    def test_clients_is_valid(self) -> None:
        """clients は有効なシャード種別"""
        kind: ShardKind = "clients"
        assert kind == "clients"

    @pytest.mark.unit
    def test_vendors_is_valid(self) -> None:
        """vendors は有効なシャード種別"""
        kind: ShardKind = "vendors"
        assert kind == "vendors"

    @pytest.mark.unit
    def test_knowledge_is_valid(self) -> None:
        """knowledge は有効なシャード種別"""
        kind: ShardKind = "knowledge"
        assert kind == "knowledge"

    @pytest.mark.unit
    def test_shard_kinds_constant_has_all_four(self) -> None:
        """SHARD_KINDS 定数に4種全て含まれる"""
        assert "projects" in SHARD_KINDS
        assert "clients" in SHARD_KINDS
        assert "vendors" in SHARD_KINDS
        assert "knowledge" in SHARD_KINDS
        assert len(SHARD_KINDS) == 4

    @pytest.mark.unit
    def test_shard_kinds_is_tuple(self) -> None:
        """SHARD_KINDS は immutable な tuple"""
        assert isinstance(SHARD_KINDS, tuple)


# =============================================================================
# ShardEntity
# =============================================================================


class TestShardEntity:
    """ShardEntity TypedDict のテスト"""

    @pytest.mark.unit
    def test_has_kind_field(self) -> None:
        """kind フィールド（ShardKind）"""
        hints = get_type_hints(ShardEntity)
        assert "kind" in hints

    @pytest.mark.unit
    def test_has_canonical_name_field(self) -> None:
        """canonical_name フィールド（正式名称）"""
        hints = get_type_hints(ShardEntity)
        assert "canonical_name" in hints
        assert hints["canonical_name"] is str

    @pytest.mark.unit
    def test_has_slug_field(self) -> None:
        """slug フィールド（ファイル名/ディレクトリ名用ASCII）"""
        hints = get_type_hints(ShardEntity)
        assert "slug" in hints
        assert hints["slug"] is str

    @pytest.mark.unit
    def test_has_aliases_field(self) -> None:
        """aliases フィールド（別名リスト）"""
        hints = get_type_hints(ShardEntity)
        assert "aliases" in hints
        assert hints["aliases"] == List[str]

    @pytest.mark.unit
    def test_has_archived_field(self) -> None:
        """archived フィールド（アーカイブ済みフラグ）"""
        hints = get_type_hints(ShardEntity)
        assert "archived" in hints
        assert hints["archived"] is bool

    @pytest.mark.unit
    def test_has_category_field(self) -> None:
        """category フィールド（knowledge シャードのカテゴリ、None 許容）"""
        hints = get_type_hints(ShardEntity)
        assert "category" in hints
        assert hints["category"] == Optional[str]

    @pytest.mark.unit
    def test_can_construct_project_entity(self) -> None:
        """案件エンティティの構築"""
        entity: ShardEntity = {
            "kind": "projects",
            "canonical_name": "○○マンション新築工事",
            "slug": "MaruMaruMansion",
            "aliases": ["○○MS", "現場番号2026-003", "○○町案件"],
            "archived": False,
            "category": None,
        }
        assert entity["kind"] == "projects"
        assert entity["archived"] is False

    @pytest.mark.unit
    def test_can_construct_knowledge_entity_with_category(self) -> None:
        """知見エンティティ（カテゴリ付き）の構築"""
        entity: ShardEntity = {
            "kind": "knowledge",
            "canonical_name": "排煙告示",
            "slug": "smoke-evacuation-notice",
            "aliases": ["排煙設備", "告示1436号"],
            "archived": False,
            "category": "法規",
        }
        assert entity["category"] == "法規"

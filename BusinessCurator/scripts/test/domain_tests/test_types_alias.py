#!/usr/bin/env python3
"""
domain/types/alias.py テスト
============================

AliasRecord TypedDict のフィールド検証。

設計意図:
- _alias_resolver.md の1エントリのドメイン表現
- ResolverService の add/edit/remove/complete_archive/rebuild が扱う単位
- archive_status で active/completed/removed の 3 状態を表現
"""

from typing import get_type_hints

import pytest

from domain.types.alias import AliasRecord

# =============================================================================
# AliasRecord
# =============================================================================


class TestAliasRecord:
    """AliasRecord TypedDict のテスト（業務計画書 §4.3 準拠）"""

    @pytest.mark.unit
    def test_has_id_field(self) -> None:
        """id フィールド（kind/slug 複合キー、例 "projects/MaruMaruMansion"）"""
        hints = get_type_hints(AliasRecord)
        assert "id" in hints
        assert hints["id"] is str

    @pytest.mark.unit
    def test_has_canonical_field(self) -> None:
        """canonical フィールド（正式名称、md リンクテキストになる）"""
        hints = get_type_hints(AliasRecord)
        assert "canonical" in hints
        assert hints["canonical"] is str

    @pytest.mark.unit
    def test_has_aliases_field(self) -> None:
        """aliases フィールド（also[] のリスト）"""
        hints = get_type_hints(AliasRecord)
        assert "aliases" in hints
        assert hints["aliases"] == list[str]

    @pytest.mark.unit
    def test_has_shard_field(self) -> None:
        """shard フィールド（ShardKind）"""
        hints = get_type_hints(AliasRecord)
        assert "shard" in hints

    @pytest.mark.unit
    def test_has_target_path_field(self) -> None:
        """target_path フィールド（リンク先 md パス、文字列）"""
        hints = get_type_hints(AliasRecord)
        assert "target_path" in hints
        assert hints["target_path"] is str

    @pytest.mark.unit
    def test_has_archive_status_field(self) -> None:
        """archive_status フィールド（active/completed/removed の 3 状態）"""
        hints = get_type_hints(AliasRecord)
        assert "archive_status" in hints

    @pytest.mark.unit
    def test_can_construct_active_project(self) -> None:
        """活性案件のレコード構築"""
        rec: AliasRecord = {
            "id": "projects/MaruMaruMansion",
            "canonical": "○○マンション新築工事",
            "aliases": ["○○MS", "現場番号2026-003", "○○町案件"],
            "shard": "projects",
            "target_path": "shards/projects/MaruMaruMansion/_project.md",
            "archive_status": "active",
        }
        assert rec["shard"] == "projects"
        assert rec["archive_status"] == "active"

    @pytest.mark.unit
    def test_can_construct_completed_project(self) -> None:
        """完工アーカイブ案件のレコード構築（archive_status='completed'）"""
        rec: AliasRecord = {
            "id": "projects/BatsuBatsuBiru",
            "canonical": "完工済み：××ビル改修工事",
            "aliases": ["××ビル", "現場番号2025-018"],
            "shard": "projects",
            "target_path": "archive/projects/BatsuBatsuBiru/_project.md",
            "archive_status": "completed",
        }
        assert rec["archive_status"] == "completed"
        assert "archive/" in rec["target_path"]

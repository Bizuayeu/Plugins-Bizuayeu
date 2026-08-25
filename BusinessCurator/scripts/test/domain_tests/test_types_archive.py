#!/usr/bin/env python3
"""
domain/types/archive.py テスト
==============================

ArchiveManifest TypedDict のフィールド検証。

設計意図:
- archive/projects/{Name}/_archive_manifest.json として保存される
- ArchiveOrchestrator が生成、md スキルが内容を読んで報告
- 抽出された知見記事の参照を保持
"""

from typing import get_type_hints

import pytest

from domain.types.archive import ArchiveManifest, ExtractedKnowledge

# =============================================================================
# ExtractedKnowledge
# =============================================================================


class TestExtractedKnowledge:
    """ExtractedKnowledge TypedDict のテスト"""

    @pytest.mark.unit
    def test_has_title_field(self) -> None:
        """title フィールド（知見記事タイトル）"""
        hints = get_type_hints(ExtractedKnowledge)
        assert "title" in hints
        assert hints["title"] is str

    @pytest.mark.unit
    def test_has_target_path_field(self) -> None:
        """target_path フィールド（保存先 md パス）"""
        hints = get_type_hints(ExtractedKnowledge)
        assert "target_path" in hints
        assert hints["target_path"] is str

    @pytest.mark.unit
    def test_has_category_field(self) -> None:
        """category フィールド（知見カテゴリ）"""
        hints = get_type_hints(ExtractedKnowledge)
        assert "category" in hints
        assert hints["category"] is str


# =============================================================================
# ArchiveManifest
# =============================================================================


class TestArchiveManifest:
    """ArchiveManifest TypedDict のテスト"""

    @pytest.mark.unit
    def test_has_project_slug_field(self) -> None:
        """project_slug フィールド（アーカイブ対象案件 slug）"""
        hints = get_type_hints(ArchiveManifest)
        assert "project_slug" in hints
        assert hints["project_slug"] is str

    @pytest.mark.unit
    def test_has_project_canonical_field(self) -> None:
        """project_canonical フィールド（正式名称）"""
        hints = get_type_hints(ArchiveManifest)
        assert "project_canonical" in hints
        assert hints["project_canonical"] is str

    @pytest.mark.unit
    def test_has_archived_at_field(self) -> None:
        """archived_at フィールド（ISO 8601 文字列）"""
        hints = get_type_hints(ArchiveManifest)
        assert "archived_at" in hints
        assert hints["archived_at"] is str

    @pytest.mark.unit
    def test_has_reason_field(self) -> None:
        """reason フィールド（アーカイブ理由）"""
        hints = get_type_hints(ArchiveManifest)
        assert "reason" in hints
        assert hints["reason"] is str

    @pytest.mark.unit
    def test_has_source_path_field(self) -> None:
        """source_path フィールド（移動元、shards/projects/{slug}/）"""
        hints = get_type_hints(ArchiveManifest)
        assert "source_path" in hints
        assert hints["source_path"] is str

    @pytest.mark.unit
    def test_has_destination_path_field(self) -> None:
        """destination_path フィールド（移動先、archive/projects/{slug}/）"""
        hints = get_type_hints(ArchiveManifest)
        assert "destination_path" in hints
        assert hints["destination_path"] is str

    @pytest.mark.unit
    def test_has_extracted_knowledge_field(self) -> None:
        """extracted_knowledge フィールド（抽出された知見記事のリスト）"""
        hints = get_type_hints(ArchiveManifest)
        assert "extracted_knowledge" in hints
        assert hints["extracted_knowledge"] == list[ExtractedKnowledge]

    @pytest.mark.unit
    def test_can_construct(self) -> None:
        """マニフェスト構築"""
        knowledge: ExtractedKnowledge = {
            "title": "排煙計算の実務ノート",
            "target_path": "shards/knowledge/法規/smoke-evacuation-practice.md",
            "category": "法規",
        }
        manifest: ArchiveManifest = {
            "project_slug": "BatsuBatsuBiru",
            "project_canonical": "××ビル改修工事",
            "archived_at": "2026-04-07T15:00:00+09:00",
            "reason": "完工",
            "source_path": "shards/projects/BatsuBatsuBiru/",
            "destination_path": "archive/projects/BatsuBatsuBiru/",
            "extracted_knowledge": [knowledge],
        }
        assert manifest["project_slug"] == "BatsuBatsuBiru"
        assert len(manifest["extracted_knowledge"]) == 1

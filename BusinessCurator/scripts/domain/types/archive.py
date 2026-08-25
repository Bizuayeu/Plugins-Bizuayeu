#!/usr/bin/env python3
"""
Archive Domain Types
====================

archive/projects/{Name}/_archive_manifest.json のドメイン表現。

設計意図:
- ArchiveOrchestrator が生成、md スキルが内容を読んで報告に使う
- 案件アーカイブ時に抽出された知見記事の参照を保持
- 業務計画書 §3.4 知見抽出フェーズの永続化
"""

from typing import TypedDict


class ExtractedKnowledge(TypedDict):
    """
    アーカイブ時に抽出された知見記事のメタデータ

    Attributes:
        title: 知見記事タイトル
        target_path: 保存先 md パス（plugin_root 相対）
        category: 知見カテゴリ（knowledge シャード内）
    """

    title: str
    target_path: str
    category: str


class ArchiveManifest(TypedDict):
    """
    案件アーカイブのマニフェスト

    Attributes:
        project_slug: アーカイブ対象案件の slug
        project_canonical: 正式名称
        archived_at: アーカイブ実行時刻（ISO 8601 文字列）
        reason: アーカイブ理由（"完工" 等）
        source_path: 移動元（shards/projects/{slug}/）
        destination_path: 移動先（archive/projects/{slug}/）
        extracted_knowledge: 抽出された知見記事のリスト
    """

    project_slug: str
    project_canonical: str
    archived_at: str
    reason: str
    source_path: str
    destination_path: str
    extracted_knowledge: list[ExtractedKnowledge]


__all__ = ["ArchiveManifest", "ExtractedKnowledge"]

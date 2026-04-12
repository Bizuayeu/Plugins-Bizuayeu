#!/usr/bin/env python3
"""
domain/types/alias.py ArchiveStatus テスト
==========================================

archive_status Literal 型と ARCHIVE_STATUSES 定数のテスト。

設計意図:
- `archive_status: Literal["active", "completed", "removed"]` は
  v4 で `archived: bool` を置き換えた単一の真実源
- active: 通常運用中
- completed: 完工アーカイブ（target_path は archive/<kind>/X 配下）
- removed: 誤登録/取引停止/統合による論理削除
"""

from typing import get_type_hints

import pytest

from domain.types.alias import AliasRecord
from domain.types.shard import ARCHIVE_STATUSES, ArchiveStatus, ShardEntity


class TestArchiveStatusesConstant:
    """ARCHIVE_STATUSES 定数のテスト"""

    @pytest.mark.unit
    def test_archive_statuses_is_tuple(self) -> None:
        """ARCHIVE_STATUSES は immutable tuple"""
        assert isinstance(ARCHIVE_STATUSES, tuple)

    @pytest.mark.unit
    def test_archive_statuses_has_three_values(self) -> None:
        """ARCHIVE_STATUSES は 3 状態のみ"""
        assert len(ARCHIVE_STATUSES) == 3

    @pytest.mark.unit
    def test_archive_statuses_contains_active_completed_removed(self) -> None:
        """active, completed, removed が全て含まれる"""
        assert "active" in ARCHIVE_STATUSES
        assert "completed" in ARCHIVE_STATUSES
        assert "removed" in ARCHIVE_STATUSES


class TestAliasRecordArchiveStatus:
    """AliasRecord に archive_status フィールドが存在することのテスト"""

    @pytest.mark.unit
    def test_archive_status_field_exists(self) -> None:
        """archive_status フィールドが型ヒントに存在"""
        hints = get_type_hints(AliasRecord)
        assert "archive_status" in hints

    @pytest.mark.unit
    def test_archived_field_removed(self) -> None:
        """旧 archived フィールドは v4 で廃止済み"""
        hints = get_type_hints(AliasRecord)
        assert "archived" not in hints

    @pytest.mark.unit
    def test_can_construct_active_record(self) -> None:
        """archive_status='active' でレコード構築可能"""
        rec: AliasRecord = {
            "id": "projects/MaruMaruMansion",
            "canonical": "○○マンション新築工事",
            "aliases": ["○○MS"],
            "shard": "projects",
            "target_path": "shards/projects/MaruMaruMansion/_project.md",
            "archive_status": "active",
        }
        assert rec["archive_status"] == "active"

    @pytest.mark.unit
    def test_can_construct_completed_record(self) -> None:
        """archive_status='completed' でレコード構築可能（完工アーカイブ）"""
        rec: AliasRecord = {
            "id": "projects/MukojimaSumida",
            "canonical": "完工：墨田区向島",
            "aliases": [],
            "shard": "projects",
            "target_path": "archive/projects/MukojimaSumida/_project.md",
            "archive_status": "completed",
        }
        assert rec["archive_status"] == "completed"
        assert "archive/" in rec["target_path"]

    @pytest.mark.unit
    def test_can_construct_removed_record(self) -> None:
        """archive_status='removed' でレコード構築可能（論理削除）"""
        rec: AliasRecord = {
            "id": "vendors/YamaguchiInd",
            "canonical": "山口工業",
            "aliases": ["yamaguchi-ind.co.jp"],
            "shard": "vendors",
            "target_path": "shards/vendors/YamaguchiInd.md",
            "archive_status": "removed",
        }
        assert rec["archive_status"] == "removed"


class TestShardEntityArchiveStatus:
    """ShardEntity に archive_status フィールドが存在することのテスト"""

    @pytest.mark.unit
    def test_archive_status_field_exists(self) -> None:
        hints = get_type_hints(ShardEntity)
        assert "archive_status" in hints

    @pytest.mark.unit
    def test_archived_field_removed(self) -> None:
        hints = get_type_hints(ShardEntity)
        assert "archived" not in hints

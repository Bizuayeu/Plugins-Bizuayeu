#!/usr/bin/env python3
"""
domain/constants.py テスト
==========================

ドメイン定数のテスト。

設計意図:
- マジックナンバー/マジックストリングを排除
- ディレクトリ名・閾値を1ファイルに集約
- 変更時の影響範囲を限定
"""

import pytest

from domain import constants

# =============================================================================
# シャード定数
# =============================================================================


class TestShardConstants:
    """シャード関連定数"""

    @pytest.mark.unit
    def test_shard_kinds_re_exported(self) -> None:
        """SHARD_KINDS が constants からも参照可能"""
        assert hasattr(constants, "SHARD_KINDS")
        assert "projects" in constants.SHARD_KINDS

    @pytest.mark.unit
    def test_unclassified_dir_name(self) -> None:
        """UNCLASSIFIED_DIR_NAME 定数"""
        assert hasattr(constants, "UNCLASSIFIED_DIR_NAME")
        assert constants.UNCLASSIFIED_DIR_NAME == "unclassified"

    @pytest.mark.unit
    def test_raw_entries_dir_name(self) -> None:
        """RAW_ENTRIES_DIR_NAME 定数"""
        assert hasattr(constants, "RAW_ENTRIES_DIR_NAME")
        assert constants.RAW_ENTRIES_DIR_NAME == "raw-entries"

    @pytest.mark.unit
    def test_inbox_dir_name(self) -> None:
        """INBOX_DIR_NAME 定数"""
        assert hasattr(constants, "INBOX_DIR_NAME")
        assert constants.INBOX_DIR_NAME == "inbox"

    @pytest.mark.unit
    def test_shards_dir_name(self) -> None:
        """SHARDS_DIR_NAME 定数"""
        assert hasattr(constants, "SHARDS_DIR_NAME")
        assert constants.SHARDS_DIR_NAME == "shards"

    @pytest.mark.unit
    def test_archive_dir_name(self) -> None:
        """ARCHIVE_DIR_NAME 定数"""
        assert hasattr(constants, "ARCHIVE_DIR_NAME")
        assert constants.ARCHIVE_DIR_NAME == "archive"

    @pytest.mark.unit
    def test_triage_logs_dir_name(self) -> None:
        """TRIAGE_LOGS_DIR_NAME 定数"""
        assert hasattr(constants, "TRIAGE_LOGS_DIR_NAME")
        assert constants.TRIAGE_LOGS_DIR_NAME == "triage_logs"


# =============================================================================
# triage 閾値
# =============================================================================


class TestTriageConstants:
    """triage 関連定数"""

    @pytest.mark.unit
    def test_default_triage_threshold(self) -> None:
        """DEFAULT_TRIAGE_THRESHOLD 定数（ルール優先からLLMフォールバックへの境界）"""
        assert hasattr(constants, "DEFAULT_TRIAGE_THRESHOLD")
        assert isinstance(constants.DEFAULT_TRIAGE_THRESHOLD, float)
        assert 0.0 <= constants.DEFAULT_TRIAGE_THRESHOLD <= 1.0


# =============================================================================
# ファイル命名
# =============================================================================


class TestFileNamingConstants:
    """ファイル命名関連定数"""

    @pytest.mark.unit
    def test_entry_id_prefix(self) -> None:
        """ENTRY_ID_PREFIX 定数（email_）"""
        assert hasattr(constants, "ENTRY_ID_PREFIX")
        assert constants.ENTRY_ID_PREFIX == "email_"

    @pytest.mark.unit
    def test_entry_id_hash_length(self) -> None:
        """ENTRY_ID_HASH_LENGTH 定数（衝突回避用ハッシュ桁数）"""
        assert hasattr(constants, "ENTRY_ID_HASH_LENGTH")
        assert isinstance(constants.ENTRY_ID_HASH_LENGTH, int)
        assert constants.ENTRY_ID_HASH_LENGTH >= 6

    @pytest.mark.unit
    def test_alias_resolver_filename(self) -> None:
        """ALIAS_RESOLVER_FILENAME 定数"""
        assert hasattr(constants, "ALIAS_RESOLVER_FILENAME")
        assert constants.ALIAS_RESOLVER_FILENAME == "_alias_resolver.md"

    @pytest.mark.unit
    def test_root_wiki_filename(self) -> None:
        """ROOT_WIKI_FILENAME 定数"""
        assert hasattr(constants, "ROOT_WIKI_FILENAME")
        assert constants.ROOT_WIKI_FILENAME == "_root.md"

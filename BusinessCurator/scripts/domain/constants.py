#!/usr/bin/env python3
"""
Domain Constants
================

ドメイン横断の定数定義。

設計意図:
- マジックナンバー/マジックストリングを排除
- ディレクトリ名・閾値・ファイル名規約を1ファイルに集約
- 変更時の影響範囲を限定し、grep 容易性を確保
"""

from typing import Final

from domain.types.shard import SHARD_KINDS, ShardKind

# =============================================================================
# シャード関連
# =============================================================================

__all__ = [
    "ALIAS_RESOLVER_FILENAME",
    "ARCHIVE_DIR_NAME",
    "DEFAULT_TRIAGE_THRESHOLD",
    "ENTRY_ID_HASH_LENGTH",
    "ENTRY_ID_PREFIX",
    "INBOX_DIR_NAME",
    "RAW_ENTRIES_DIR_NAME",
    "ROOT_WIKI_FILENAME",
    "SHARDS_DIR_NAME",
    "SHARD_KINDS",
    "ShardKind",
    "TRIAGE_LOGS_DIR_NAME",
    "UNCLASSIFIED_DIR_NAME",
]


# =============================================================================
# ディレクトリ名
# =============================================================================

INBOX_DIR_NAME: Final[str] = "inbox"
"""inbox/ ディレクトリ名（ingest 出力先のルート）"""

RAW_ENTRIES_DIR_NAME: Final[str] = "raw-entries"
"""inbox/raw-entries/ ディレクトリ名（ingest 直接出力先）"""

UNCLASSIFIED_DIR_NAME: Final[str] = "unclassified"
"""inbox/unclassified/ ディレクトリ名（triage 保留先）"""

SHARDS_DIR_NAME: Final[str] = "shards"
"""shards/ ディレクトリ名（活性データのルート）"""

ARCHIVE_DIR_NAME: Final[str] = "archive"
"""archive/ ディレクトリ名（アーカイブ済みデータのルート）"""

TRIAGE_LOGS_DIR_NAME: Final[str] = "triage_logs"
"""triage_logs/ ディレクトリ名（日次 JSON ログ）"""


# =============================================================================
# ファイル名
# =============================================================================

ALIAS_RESOLVER_FILENAME: Final[str] = "_alias_resolver.md"
"""エイリアスリゾルバのファイル名（plugin_root 直下）"""

ROOT_WIKI_FILENAME: Final[str] = "_root.md"
"""ルート wiki のファイル名（plugin_root 直下）"""


# =============================================================================
# triage 閾値
# =============================================================================

DEFAULT_TRIAGE_THRESHOLD: Final[float] = 0.8
"""ルール優先から LLM フォールバックへの境界スコア（0.0〜1.0）"""


# =============================================================================
# エントリID生成
# =============================================================================

ENTRY_ID_PREFIX: Final[str] = "email_"
"""エントリ ID プレフィックス（source_type=email の場合）"""

ENTRY_ID_HASH_LENGTH: Final[int] = 8
"""エントリ ID 末尾の衝突回避用ハッシュ桁数"""

#!/usr/bin/env python3
"""
Multi-User Backup Domain Types
==============================

複数ユーザー Gmail バックアップ計画・状態・結果のドメイン表現。

設計意図:
- 単一ユーザー用の BackupPlan/BackupState/BackupResult は**完全不変**で流用
- MultiUserBackupState は per_user_states に BackupState を内包する構造
- message_id_index: 正規化済み Message-ID → "email::gmail_id" で所有者追跡
- dedup 方針: 「最初に遭遇した版を保存」(first-wins)
- JSON シリアライズ可能性: datetime は isoformat 文字列化して保存

Usage:
    from domain.types.multi_backup import (
        MultiUserBackupPlan,
        MultiUserBackupState,
        MultiUserBackupResult,
    )
"""

from datetime import datetime
from typing import TypedDict

from domain.types.account import GmailAccount
from domain.types.backup import BackupState, OutputFormat
from domain.types.query import SearchQuery


class MultiUserBackupPlan(TypedDict):
    """
    複数ユーザーバックアップ実行計画。

    Attributes:
        multi_plan_id: 計画識別子 (emails + query から決定的に導出)
        accounts: 対象 Gmail アカウント一覧 (30人分等)
        query: 全ユーザー共通の検索クエリ
        output_dir: 出力ディレクトリ絶対パス
        output_format: "eml" | "mbox"
    """

    multi_plan_id: str
    accounts: list[GmailAccount]
    query: SearchQuery
    output_dir: str
    output_format: OutputFormat


class MultiUserBackupState(TypedDict):
    """
    複数ユーザーバックアップの進行状態（再開機構の永続化対象）。

    Attributes:
        multi_plan_id: 対応する MultiUserBackupPlan の識別子
        per_user_states: user_email → 単一ユーザー BackupState のマップ
        message_id_index: 正規化済み Message-ID → "user_email::gmail_id"
            (first-wins 重複排除の所有者追跡)
        last_updated: 最終更新日時 (UTC aware)
        started_user_emails: 処理開始済みユーザー列
        completed_user_emails: 処理完了ユーザー列
    """

    multi_plan_id: str
    per_user_states: dict[str, BackupState]
    message_id_index: dict[str, str]
    last_updated: datetime
    started_user_emails: list[str]
    completed_user_emails: list[str]


class MultiUserBackupResult(TypedDict):
    """
    複数ユーザーバックアップ完了レポート。

    Attributes:
        multi_plan_id: 対応する MultiUserBackupPlan の識別子
        per_user_success: user_email → 新規取得成功件数
        per_user_failure: user_email → 失敗件数
        per_user_deduped: user_email → 重複でスキップされた件数
        total_unique_messages: 実書き込み件数 (重複排除後)
        total_dedup_skipped: 全ユーザー合計の重複スキップ件数
        total_messages_without_message_id: Message-ID 欠落で強制書込された件数
        output_files: 生成されたファイルパス列
        started_at: 開始日時 (UTC aware)
        finished_at: 終了日時 (UTC aware)
    """

    multi_plan_id: str
    per_user_success: dict[str, int]
    per_user_failure: dict[str, int]
    per_user_deduped: dict[str, int]
    total_unique_messages: int
    total_dedup_skipped: int
    total_messages_without_message_id: int
    output_files: list[str]
    started_at: datetime
    finished_at: datetime


__all__ = ["MultiUserBackupPlan", "MultiUserBackupResult", "MultiUserBackupState"]

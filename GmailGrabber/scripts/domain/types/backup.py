#!/usr/bin/env python3
"""
Backup Domain Types
===================

バックアップ計画・状態・結果のドメイン表現。

設計意図:
- BackupPlan: 実行指示（入力パラメータ群）
- BackupState: 進行中状態（再開機構の永続化対象）
- BackupResult: 完了結果（レポート出力用）
- plan_id はプラン同定キー（BackupPlanから決定的に導出、hash等）
- BackupState は JSON シリアライズ可能である必要がある（datetime は isoformat 文字列化）

Usage:
    from datetime import datetime
    from domain.types.backup import BackupPlan, BackupState, BackupResult
"""

from datetime import datetime
from typing import Literal, TypedDict

from domain.types.account import GmailAccount
from domain.types.query import SearchQuery

OutputFormat = Literal["eml", "mbox"]


class BackupPlan(TypedDict):
    """
    バックアップ実行計画

    Attributes:
        plan_id: 計画識別子（BackupPlan内容から決定的に導出）
        account: 対象 Gmail アカウント
        query: 検索クエリ
        output_dir: 出力ディレクトリ絶対パス
        output_format: 出力形式 ("eml" | "mbox")
    """

    plan_id: str
    account: GmailAccount
    query: SearchQuery
    output_dir: str
    output_format: OutputFormat


class BackupState(TypedDict):
    """
    バックアップ進行状態（再開機構のための永続化対象）

    Attributes:
        plan_id: 対応する BackupPlan の識別子
        fetched_ids: 取得済み Gmail message ID 列（冪等性確保）
        failed_ids: 取得失敗した ID 列（後で再試行）
        last_updated: 最終更新日時（UTC aware）
        total_estimated: 推定総件数（Gmail API resultSizeEstimate）
    """

    plan_id: str
    fetched_ids: list[str]
    failed_ids: list[str]
    last_updated: datetime
    total_estimated: int


class BackupResult(TypedDict):
    """
    バックアップ完了レポート

    Attributes:
        plan_id: 対応する BackupPlan の識別子
        success_count: 成功件数
        failure_count: 失敗件数
        output_files: 生成されたファイルパス列
        started_at: 開始日時（UTC aware）
        finished_at: 終了日時（UTC aware）
    """

    plan_id: str
    success_count: int
    failure_count: int
    output_files: list[str]
    started_at: datetime
    finished_at: datetime


__all__ = ["BackupPlan", "BackupResult", "BackupState", "OutputFormat"]

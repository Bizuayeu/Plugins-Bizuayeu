#!/usr/bin/env python3
"""
BusinessCurator カスタム例外
============================

プロジェクト固有の例外クラス階層。

設計意図:
- 汎用 Exception を具体的な例外に置き換え、デバッグを容易にする
- DiagnosticContext で構造化エラー情報を保持
- EpisodicRAG exceptions.py のパターン踏襲

Usage:
    from domain.exceptions import (
        BusinessCuratorError, IngestError, TriageError,
        ResolverError, ArchiveError, EntityNotFoundError,
        DiagnosticContext,
    )

    ctx = DiagnosticContext(operation="ingest", entry_id="email_001")
    raise IngestError("parse failed", context=ctx)
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class DiagnosticContext:
    """
    エラー診断用コンテキスト情報

    エラー発生時の状態を保持し、デバッグを支援する。
    全フィールドはオプショナル。`additional_info` で任意のキーを追加可能。

    Attributes:
        operation: 実行中の操作名（"ingest", "triage", "archive" 等）
        entry_id: 対象エントリID
        file_path: 関連ファイルパス
        shard_kind: 関連シャード種別
        file_count: 処理中のファイル数
        additional_info: その他の任意情報
    """

    operation: Optional[str] = None
    entry_id: Optional[str] = None
    file_path: Optional[Path] = None
    shard_kind: Optional[str] = None
    file_count: Optional[int] = None
    additional_info: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """
        非 None 値のみを含む辞書を返す

        Returns:
            キー=属性名、値=属性値の辞書（None は除外）
        """
        result: Dict[str, Any] = {}
        if self.operation is not None:
            result["operation"] = self.operation
        if self.entry_id is not None:
            result["entry_id"] = self.entry_id
        if self.file_path is not None:
            result["file_path"] = str(self.file_path)
        if self.shard_kind is not None:
            result["shard_kind"] = self.shard_kind
        if self.file_count is not None:
            result["file_count"] = self.file_count
        if self.additional_info:
            result.update(self.additional_info)
        return result

    def __str__(self) -> str:
        """コンテキスト情報の文字列表現（key=value, ...）"""
        items = self.to_dict()
        if not items:
            return ""
        return ", ".join(f"{k}={v}" for k, v in items.items())


class BusinessCuratorError(Exception):
    """
    BusinessCurator 基底例外

    全てのプロジェクト固有例外の親クラス。
    `except BusinessCuratorError` で全カスタム例外をキャッチ可能。
    """

    def __init__(self, message: str, context: Optional[DiagnosticContext] = None) -> None:
        """
        Args:
            message: エラーメッセージ
            context: 診断コンテキスト（オプション）
        """
        self.context = context
        super().__init__(message)

    def __str__(self) -> str:
        """エラーメッセージの文字列表現（コンテキスト付き）"""
        base = super().__str__()
        if self.context:
            ctx_str = str(self.context)
            if ctx_str:
                return f"{base} [Context: {ctx_str}]"
        return base


class IngestError(BusinessCuratorError):
    """
    ingest フェーズのエラー

    Examples:
        - メールパース失敗
        - .eml/.mbox フォーマット不正
        - raw-entries 書き込み失敗
    """

    pass


class TriageError(BusinessCuratorError):
    """
    triage フェーズのエラー

    Examples:
        - ルールパターンのコンパイル失敗
        - LLM フォールバック呼び出し失敗
        - triage_log 書き込み失敗
    """

    pass


class ResolverError(BusinessCuratorError):
    """
    エイリアスリゾルバのエラー

    Examples:
        - 重複 ID
        - _alias_resolver.md パース失敗
        - rebuild 中の整合性違反
    """

    pass


class ArchiveError(BusinessCuratorError):
    """
    archive フェーズのエラー

    Examples:
        - 移動先既存
        - manifest 生成失敗
        - resolver 更新失敗
    """

    pass


class EntityNotFoundError(BusinessCuratorError):
    """
    エンティティ未登録エラー

    Examples:
        - resolver にない slug を指定
        - 存在しないシャード参照
    """

    pass


__all__ = [
    "ArchiveError",
    "BusinessCuratorError",
    "DiagnosticContext",
    "EntityNotFoundError",
    "IngestError",
    "ResolverError",
    "TriageError",
]

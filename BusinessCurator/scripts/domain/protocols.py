#!/usr/bin/env python3
"""
Domain Protocols
================

依存関係逆転（DIP）のための Protocol 定義。

設計意図:
- application 層は Protocol にのみ依存
- infrastructure 層が Protocol を実装（具象クラス）
- テストでは Fake/Mock を application UseCase に注入
- 循環インポート回避

定義 Protocol:
- ClockProtocol: 時刻取得（テストで FakeClock 注入可能）
- EmailParserProtocol: メールパース（.eml/.mbox）
- EntryRepositoryProtocol: raw-entries の永続化
- AliasResolverRepositoryProtocol: _alias_resolver.md の永続化
- TriageLogRepositoryProtocol: triage_logs/ の永続化
- LLMTriageProtocol: LLM フォールバック分類（claude -p subprocess 経由）

Usage:
    from domain.protocols import EntryRepositoryProtocol

    class IngestBatchUseCase:
        def __init__(self, repo: EntryRepositoryProtocol) -> None:
            self._repo = repo
"""

from datetime import datetime
from pathlib import Path
from typing import Protocol, runtime_checkable

from domain.types.alias import AliasRecord
from domain.types.email import EmailMessage
from domain.types.entry import RawEntry
from domain.types.shard import ShardKind
from domain.types.triage import TriageLogEntry

__all__ = [
    "AliasResolverRepositoryProtocol",
    "ClockProtocol",
    "EmailParserProtocol",
    "EntryRepositoryProtocol",
    "LLMTriageProtocol",
    "TriageLogRepositoryProtocol",
]


# =============================================================================
# ClockProtocol
# =============================================================================


@runtime_checkable
class ClockProtocol(Protocol):
    """
    時刻取得 Protocol

    テストでは FakeClock を注入することで決定的時刻を提供する。
    本番では SystemClock（infrastructure/clock.py）が実装。
    """

    def now(self) -> datetime:
        """
        現在時刻を返す

        Returns:
            タイムゾーン情報を含む datetime（実装側で aware を保証）
        """
        ...


# =============================================================================
# EmailParserProtocol
# =============================================================================


@runtime_checkable
class EmailParserProtocol(Protocol):
    """
    メールパーサー Protocol

    .eml / .mbox ファイルから EmailMessage を生成する。
    実装: EmlEmailParser, MboxEmailParser（infrastructure/email_parser/）
    """

    def parse(self, path: Path) -> EmailMessage:
        """
        単一メールファイルをパース

        Args:
            path: .eml ファイルパス

        Returns:
            EmailMessage（パース済み中間表現）

        Raises:
            IngestError: パース失敗
        """
        ...

    def parse_many(self, path: Path) -> list[EmailMessage]:
        """
        複数メール（mbox 等）をパース

        Args:
            path: .mbox ファイルパス（または .eml 単体）

        Returns:
            EmailMessage のリスト（順序保持）

        Raises:
            IngestError: パース失敗
        """
        ...


# =============================================================================
# EntryRepositoryProtocol
# =============================================================================


@runtime_checkable
class EntryRepositoryProtocol(Protocol):
    """
    RawEntry の永続化 Protocol

    inbox/raw-entries/ への読み書きを抽象化。
    実装: FileEntryRepository（infrastructure/repositories/entry_repository.py）
    """

    def save(self, entry: RawEntry) -> None:
        """
        エントリを永続化（冪等：既存なら上書き）

        Args:
            entry: 保存対象エントリ
        """
        ...

    def exists(self, entry_id: str) -> bool:
        """
        エントリ ID の存在確認

        Args:
            entry_id: エントリ ID

        Returns:
            存在すれば True
        """
        ...

    def load(self, entry_id: str) -> RawEntry:
        """
        エントリを読み込む

        Args:
            entry_id: エントリ ID

        Returns:
            RawEntry

        Raises:
            EntityNotFoundError: ID が存在しない
        """
        ...

    def list_all(self) -> list[RawEntry]:
        """
        全エントリを返す

        Returns:
            RawEntry のリスト（順序は実装依存）
        """
        ...


# =============================================================================
# AliasResolverRepositoryProtocol
# =============================================================================


@runtime_checkable
class AliasResolverRepositoryProtocol(Protocol):
    """
    エイリアスリゾルバの永続化 Protocol

    _alias_resolver.md の読み書きを抽象化。
    実装: MarkdownAliasResolverRepository
    """

    def load_all(self) -> list[AliasRecord]:
        """
        全レコードを読み込む

        Returns:
            AliasRecord のリスト

        Raises:
            ResolverError: パース失敗
        """
        ...

    def save_all(self, records: list[AliasRecord]) -> None:
        """
        全レコードを書き出す（冪等：完全置換）

        Args:
            records: 保存対象レコード
        """
        ...


# =============================================================================
# TriageLogRepositoryProtocol
# =============================================================================


@runtime_checkable
class TriageLogRepositoryProtocol(Protocol):
    """
    triage 判定ログの永続化 Protocol

    triage_logs/_triage_log_YYYYMMDD.json の読み書きを抽象化。
    実装: JsonTriageLogRepository
    """

    def append(self, log_entry: TriageLogEntry) -> None:
        """
        ログエントリを追記（日次ファイルへ）

        Args:
            log_entry: 追記対象
        """
        ...

    def load_for_date(self, date: str) -> list[TriageLogEntry]:
        """
        指定日のログを取得

        Args:
            date: YYYY-MM-DD 形式

        Returns:
            TriageLogEntry のリスト（時刻順）
        """
        ...


# =============================================================================
# LLMTriageProtocol
# =============================================================================


@runtime_checkable
class LLMTriageProtocol(Protocol):
    """
    LLM フォールバック分類 Protocol

    ルールベース triage で確定できないエントリを LLM で分類する。
    実装: ClaudeCliTriageClient（subprocess.run(["claude","-p",prompt]) 経由）
    テスト: FakeLLMTriageClient（dict 駆動の固定応答）
    """

    def classify(self, entry: RawEntry) -> ShardKind:
        """
        エントリを4シャードのいずれかに分類

        Args:
            entry: 分類対象エントリ

        Returns:
            ShardKind（projects/clients/vendors/knowledge）

        Raises:
            TriageError: LLM 呼び出し失敗、または不正レスポンス
        """
        ...

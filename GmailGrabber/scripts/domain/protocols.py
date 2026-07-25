#!/usr/bin/env python3
"""
Domain Protocols
================

依存関係逆転（DIP）のための Protocol 定義。

設計意図:
- application 層は Protocol にのみ依存
- infrastructure 層が Protocol を実装（具象クラス）
- テストでは Fake を application UseCase に注入
- 循環インポート回避

定義 Protocol (v0.1.0):
- ClockProtocol: 時刻取得
- CredentialsProviderProtocol: OAuth credentials のロード・保存・認証フロー
- GmailClientProtocol: Gmail API クライアント（search, fetch, labels）
- MessageWriterProtocol: メッセージ → ファイル書き出し
- StateRepositoryProtocol: BackupState の永続化

定義 Protocol (v0.2.0 追加):
- ServiceAccountProviderProtocol: Service Account credentials の load/impersonate
- GmailClientFactoryProtocol: user email から GmailClient を生成するファクトリ
- MultiUserStateRepositoryProtocol: MultiUserBackupState の永続化
"""

from datetime import datetime
from typing import Iterator, List, Optional, Protocol, runtime_checkable

from domain.types.backup import BackupState
from domain.types.credentials import OAuthCredentials
from domain.types.message import GmailMessage
from domain.types.multi_backup import MultiUserBackupState
from domain.types.service_account import ServiceAccountCredentials


@runtime_checkable
class ClockProtocol(Protocol):
    """時刻取得 Protocol（テストで FakeClock 注入）"""

    def now(self) -> datetime:
        """現在時刻を UTC aware datetime で返す"""
        ...


@runtime_checkable
class CredentialsProviderProtocol(Protocol):
    """OAuth 認証情報の取得・保存 Protocol"""

    def load(self, token_path: str) -> Optional[OAuthCredentials]:
        """既存 token ファイルから credentials をロード（無ければ None）"""
        ...

    def save(self, credentials: OAuthCredentials, token_path: str) -> None:
        """credentials を token ファイルに保存"""
        ...

    def authenticate_interactive(
        self, client_secret_path: str, scopes: List[str]
    ) -> OAuthCredentials:
        """ブラウザベースの対話的OAuth認証フローを実行して新規credentialsを取得"""
        ...

    def refresh(self, credentials: OAuthCredentials) -> OAuthCredentials:
        """期限切れ credentials をリフレッシュ"""
        ...


@runtime_checkable
class GmailClientProtocol(Protocol):
    """Gmail API クライアント Protocol"""

    def list_message_ids(self, query: str, max_results: Optional[int] = None) -> Iterator[str]:
        """検索クエリに一致するメッセージIDを列挙（ページング対応）"""
        ...

    def fetch_message(self, message_id: str) -> GmailMessage:
        """単一メッセージを raw 形式で取得"""
        ...

    def list_labels(self) -> List[dict]:
        """全ラベル一覧を取得 ({id, name, type} の dict 列)"""
        ...

    def estimate_count(self, query: str) -> int:
        """検索結果の推定件数（Gmail API resultSizeEstimate）"""
        ...


@runtime_checkable
class MessageWriterProtocol(Protocol):
    """メッセージをファイルに書き出す Protocol"""

    def write(self, message: GmailMessage, output_dir: str) -> str:
        """メッセージを output_dir に書き出し、生成ファイルパスを返す"""
        ...

    def finalize(self, output_dir: str) -> List[str]:
        """
        バッチ完了時の最終化処理。
        .eml writer: no-op でファイルパス列を返す。
        .mbox writer: mbox ファイルをクローズし、単一パスを返す。
        """
        ...


@runtime_checkable
class StateRepositoryProtocol(Protocol):
    """BackupState の永続化 Protocol"""

    def load(self, plan_id: str, state_dir: str) -> Optional[BackupState]:
        """plan_id に対応する state をロード（無ければ None）"""
        ...

    def save(self, state: BackupState, state_dir: str) -> None:
        """state を永続化"""
        ...

    def delete(self, plan_id: str, state_dir: str) -> None:
        """state を削除（バックアップ完了時のクリーンアップ）"""
        ...


# =============================================================================
# v0.2.0: Multi-User Service Account Protocols
# =============================================================================


@runtime_checkable
class ServiceAccountProviderProtocol(Protocol):
    """Service Account credentials の load / impersonate Protocol"""

    def load_service_account(self, key_path: str) -> ServiceAccountCredentials:
        """Service Account JSON key ファイルをロード"""
        ...

    def impersonate(
        self,
        credentials: ServiceAccountCredentials,
        subject_email: str,
        scopes: List[str],
    ) -> ServiceAccountCredentials:
        """subject を差し替えた新 credentials を返す (immutable)"""
        ...


@runtime_checkable
class GmailClientFactoryProtocol(Protocol):
    """user email から GmailClient を生成するファクトリ"""

    def create_for_user(self, user_email: str) -> "GmailClientProtocol":
        """指定 user を impersonate した Gmail client を生成"""
        ...


@runtime_checkable
class MultiUserStateRepositoryProtocol(Protocol):
    """MultiUserBackupState の永続化 Protocol"""

    def load(self, multi_plan_id: str, state_dir: str) -> Optional[MultiUserBackupState]:
        """multi_plan_id に対応する state をロード"""
        ...

    def save(self, state: MultiUserBackupState, state_dir: str) -> None:
        """state を永続化"""
        ...

    def delete(self, multi_plan_id: str, state_dir: str) -> None:
        """state を削除"""
        ...


__all__ = [
    "ClockProtocol",
    "CredentialsProviderProtocol",
    "GmailClientFactoryProtocol",
    "GmailClientProtocol",
    "MessageWriterProtocol",
    "MultiUserStateRepositoryProtocol",
    "ServiceAccountProviderProtocol",
    "StateRepositoryProtocol",
]

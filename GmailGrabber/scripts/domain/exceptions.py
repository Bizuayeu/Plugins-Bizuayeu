#!/usr/bin/env python3
"""
Domain Exceptions
=================

GmailGrabber 固有の例外階層。

設計意図:
- GmailGrabberError を基底とする単純階層
- 各層のエラーはメッセージに文脈情報を含める
- infrastructure 層の googleapiclient.errors.HttpError 等は application 層で
  ドメイン例外にラップする
"""


class GmailGrabberError(Exception):
    """GmailGrabber 例外階層の基底"""


class AuthenticationError(GmailGrabberError):
    """OAuth 認証失敗・token期限切れ等"""


class CredentialsNotFoundError(GmailGrabberError):
    """client_secret.json / token.json が見つからない"""


class GmailApiError(GmailGrabberError):
    """Gmail API 呼び出し失敗（ネットワーク・rate limit・400系）"""


class MessageNotFoundError(GmailApiError):
    """指定 message_id が Gmail に存在しない"""


class QueryBuildError(GmailGrabberError):
    """SearchQuery から Gmail 検索文字列への変換失敗"""


class ExportError(GmailGrabberError):
    """.eml / .mbox 書き出し失敗"""


class StateRepositoryError(GmailGrabberError):
    """バックアップ状態の読み書き失敗"""


class InvalidBackupPlanError(GmailGrabberError):
    """BackupPlan のバリデーション失敗"""


__all__ = [
    "AuthenticationError",
    "CredentialsNotFoundError",
    "ExportError",
    "GmailApiError",
    "GmailGrabberError",
    "InvalidBackupPlanError",
    "MessageNotFoundError",
    "QueryBuildError",
    "StateRepositoryError",
]

#!/usr/bin/env python3
"""
GoogleGmailClientFactory
========================

GmailClientFactoryProtocol の Google 実装。

Service Account JSON key から base credentials を1回ロードし、
user email ごとに .with_subject() で impersonate した GmailClient を生成する。
"""


from domain.constants import DEFAULT_SCOPES
from domain.types.service_account import ServiceAccountCredentials
from infrastructure.google_gmail.client import GoogleGmailClient
from infrastructure.google_gmail.service_account_provider import (
    GoogleServiceAccountProvider,
)


class GoogleGmailClientFactory:
    """Service Account ベースの Gmail client ファクトリ"""

    def __init__(
        self,
        service_account_key_path: str,
        scopes: list[str] | None = None,
        provider: GoogleServiceAccountProvider | None = None,
    ) -> None:
        """
        Args:
            service_account_key_path: SA JSON key ファイルパス
            scopes: 要求スコープ (デフォルト: gmail.readonly)
            provider: テスト用に注入可能 (None なら GoogleServiceAccountProvider 新規作成)
        """
        self._key_path = service_account_key_path
        self._scopes = scopes if scopes is not None else list(DEFAULT_SCOPES)
        self._provider = provider or GoogleServiceAccountProvider()
        self._base_credentials: ServiceAccountCredentials | None = None

    def create_for_user(self, user_email: str) -> GoogleGmailClient:
        """
        user_email を impersonate した GmailClient を生成。

        base credentials は初回呼び出し時に1度だけロードされ、以後キャッシュ。
        ただし各 client は独立した impersonated credentials を持つ。

        Args:
            user_email: impersonate 対象の user email

        Returns:
            GoogleGmailClient (subject=user_email で構築済み)
        """
        if self._base_credentials is None:
            self._base_credentials = self._provider.load_service_account(self._key_path)

        impersonated = self._provider.impersonate(self._base_credentials, user_email, self._scopes)
        return GoogleGmailClient(
            service_account_credentials=impersonated,
            user_id="me",
            scopes=self._scopes,
        )


__all__ = ["GoogleGmailClientFactory"]

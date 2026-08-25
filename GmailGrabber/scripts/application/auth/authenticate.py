#!/usr/bin/env python3
"""
AuthenticateUseCase
===================

OAuth 2.0 認証フロー実行ユースケース。

責務:
1. 既存 token を load
2. 存在し有効なら返す
3. 存在するが期限切れなら refresh
4. 存在しないなら interactive 認証フロー実行
5. 結果を save
"""


from domain.constants import DEFAULT_SCOPES
from domain.protocols import ClockProtocol, CredentialsProviderProtocol
from domain.types.account import GmailAccount
from domain.types.credentials import OAuthCredentials


class AuthenticateUseCase:
    """OAuth 認証ユースケース"""

    def __init__(
        self,
        credentials_provider: CredentialsProviderProtocol,
        clock: ClockProtocol,
    ) -> None:
        self._provider = credentials_provider
        self._clock = clock

    def execute(self, account: GmailAccount, scopes: list[str] | None = None) -> OAuthCredentials:
        """
        アカウントの認証情報を取得する。

        Args:
            account: 対象アカウント（credentials_path, token_path を使用）
            scopes: 要求スコープ（None ならデフォルト readonly）

        Returns:
            有効な OAuthCredentials
        """
        target_scopes = scopes if scopes is not None else DEFAULT_SCOPES

        existing = self._provider.load(account["token_path"])
        if existing is not None:
            if self._is_valid(existing):
                return existing
            # 期限切れ: refresh 試行
            if existing.get("refresh_token"):
                refreshed = self._provider.refresh(existing)
                self._provider.save(refreshed, account["token_path"])
                return refreshed

        # 新規認証フロー
        new_creds = self._provider.authenticate_interactive(
            account["credentials_path"], target_scopes
        )
        self._provider.save(new_creds, account["token_path"])
        return new_creds

    def _is_valid(self, creds: OAuthCredentials) -> bool:
        """access_token が期限内かチェック"""
        expires_at = creds.get("expires_at")
        if expires_at is None:
            return False
        return expires_at > self._clock.now()


__all__ = ["AuthenticateUseCase"]

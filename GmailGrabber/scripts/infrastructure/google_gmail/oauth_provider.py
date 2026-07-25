#!/usr/bin/env python3
"""
GoogleOAuthCredentialsProvider
==============================

CredentialsProviderProtocol の Google OAuth 2.0 実装。

使用ライブラリ:
- google-auth (token persistence, refresh)
- google-auth-oauthlib (InstalledAppFlow for browser-based auth)
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Optional

from domain.exceptions import AuthenticationError, CredentialsNotFoundError
from domain.types.credentials import OAuthCredentials


class GoogleOAuthCredentialsProvider:
    """Google OAuth 2.0 credentials の load/save/authenticate/refresh 実装"""

    def load(self, token_path: str) -> Optional[OAuthCredentials]:
        """既存 token ファイル（JSON形式）をロード"""
        path = Path(token_path)
        if not path.exists():
            return None
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            return self._from_json(raw)
        except (OSError, json.JSONDecodeError) as e:
            raise AuthenticationError(f"failed to load token from {token_path}: {e}") from e

    def save(self, credentials: OAuthCredentials, token_path: str) -> None:
        """credentials を JSON 形式で保存"""
        try:
            path = Path(token_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            serialized = self._to_json(credentials)
            path.write_text(
                json.dumps(serialized, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            # 権限を 0600 に（Unix 系のみ。Windows では no-op）
            try:
                path.chmod(0o600)
            except OSError:
                pass
        except OSError as e:
            raise AuthenticationError(f"failed to save token to {token_path}: {e}") from e

    def authenticate_interactive(
        self, client_secret_path: str, scopes: List[str]
    ) -> OAuthCredentials:
        """ブラウザベース InstalledAppFlow を実行して新規認証"""
        if not Path(client_secret_path).exists():
            raise CredentialsNotFoundError(f"client_secret file not found: {client_secret_path}")
        try:
            from google_auth_oauthlib.flow import InstalledAppFlow  # lazy import

            flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, scopes)
            google_creds = flow.run_local_server(port=0)
            return self._from_google_credentials(google_creds)
        except Exception as e:
            raise AuthenticationError(f"interactive auth failed: {e}") from e

    def refresh(self, credentials: OAuthCredentials) -> OAuthCredentials:
        """期限切れ credentials をリフレッシュ"""
        try:
            from google.auth.transport.requests import Request  # lazy import
            from google.oauth2.credentials import Credentials  # lazy import

            google_creds = Credentials(
                token=credentials["access_token"],
                refresh_token=credentials.get("refresh_token"),
                token_uri=credentials["token_uri"],
                client_id=credentials["client_id"],
                client_secret=credentials["client_secret"],
                scopes=credentials["scopes"],
            )
            google_creds.refresh(Request())
            return self._from_google_credentials(google_creds)
        except Exception as e:
            raise AuthenticationError(f"token refresh failed: {e}") from e

    # =========================================================================
    # internal serialization
    # =========================================================================

    def _to_json(self, creds: OAuthCredentials) -> dict:
        expires_at = creds.get("expires_at")
        return {
            "access_token": creds["access_token"],
            "refresh_token": creds.get("refresh_token"),
            "token_uri": creds["token_uri"],
            "client_id": creds["client_id"],
            "client_secret": creds["client_secret"],
            "scopes": list(creds["scopes"]),
            "expires_at": expires_at.isoformat() if expires_at else None,
        }

    def _from_json(self, raw: dict) -> OAuthCredentials:
        expires_at_raw = raw.get("expires_at")
        expires_at = datetime.fromisoformat(expires_at_raw) if expires_at_raw else None
        return {
            "access_token": raw["access_token"],
            "refresh_token": raw.get("refresh_token"),
            "token_uri": raw["token_uri"],
            "client_id": raw["client_id"],
            "client_secret": raw["client_secret"],
            "scopes": list(raw.get("scopes", [])),
            "expires_at": expires_at,
        }

    def _from_google_credentials(self, google_creds: Any) -> OAuthCredentials:
        """google.oauth2.credentials.Credentials → ドメイン中立 OAuthCredentials"""
        expiry = google_creds.expiry
        if expiry is not None and expiry.tzinfo is None:
            # google-auth は naive datetime を UTC として返す
            expiry = expiry.replace(tzinfo=timezone.utc)

        return {
            "access_token": google_creds.token,
            "refresh_token": google_creds.refresh_token,
            "token_uri": google_creds.token_uri,
            "client_id": google_creds.client_id,
            "client_secret": google_creds.client_secret,
            "scopes": list(google_creds.scopes or []),
            "expires_at": expiry,
        }


__all__ = ["GoogleOAuthCredentialsProvider"]

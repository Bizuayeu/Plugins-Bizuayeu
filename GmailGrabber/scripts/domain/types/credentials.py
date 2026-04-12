#!/usr/bin/env python3
"""
Credentials Domain Types
========================

OAuth 2.0 認証情報のドメイン表現。

設計意図:
- OAuthCredentials は application 層が扱うドメイン中立な認証情報
- google.oauth2.credentials.Credentials との変換は infrastructure 層
- access_token, refresh_token は機密情報 → ログ出力・シリアライゼーションで要注意
- expires_at は UTC aware datetime を期待

Usage:
    from datetime import datetime, timezone
    from domain.types.credentials import OAuthCredentials

    creds: OAuthCredentials = {
        "access_token": "ya29...",
        "refresh_token": "1//...",
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_id": "xxx.apps.googleusercontent.com",
        "client_secret": "GOCSPX-...",
        "scopes": ["https://www.googleapis.com/auth/gmail.readonly"],
        "expires_at": datetime(2026, 4, 11, 15, 0, tzinfo=timezone.utc),
    }
"""

from datetime import datetime
from typing import List, Optional, TypedDict


class OAuthCredentials(TypedDict):
    """
    OAuth 2.0 認証情報

    Attributes:
        access_token: アクセストークン（1時間で失効）
        refresh_token: リフレッシュトークン（長期保存、失効なし）
        token_uri: トークンリフレッシュエンドポイント
        client_id: OAuth クライアントID
        client_secret: OAuth クライアントシークレット
        scopes: 付与されたスコープ列
        expires_at: access_token の有効期限（UTC aware）
    """

    access_token: str
    refresh_token: Optional[str]
    token_uri: str
    client_id: str
    client_secret: str
    scopes: List[str]
    expires_at: Optional[datetime]


__all__ = ["OAuthCredentials"]

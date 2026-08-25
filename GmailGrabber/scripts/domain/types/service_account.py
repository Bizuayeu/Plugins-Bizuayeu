#!/usr/bin/env python3
"""
Service Account Credentials Domain Types
=========================================

Google Cloud Service Account JSON key のドメイン中立表現。

設計意図:
- google-auth の `service_account.Credentials.from_service_account_info` が期待する
  dict 形式と互換性がある
- `subject` フィールドを追加: Domain-Wide Delegation での impersonation 対象 user email
- infrastructure 層で `.with_subject()` を呼ぶ直前に dict から subject を除去する

Usage:
    from domain.types.service_account import ServiceAccountCredentials

    creds: ServiceAccountCredentials = {
        "type": "service_account",
        "project_id": "gmail-grabber-123",
        "private_key_id": "abc...",
        "private_key": "-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n",
        "client_email": "gmail-grabber@gmail-grabber-123.iam.gserviceaccount.com",
        "client_id": "123456789",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/...",
        "subject": "user@meguru-construction.example.jp",
    }
"""

from typing import TypedDict


class ServiceAccountCredentials(TypedDict):
    """
    Google Service Account JSON key のドメイン中立表現。

    Attributes:
        type: 固定値 "service_account"
        project_id: Google Cloud プロジェクト ID
        private_key_id: 秘密鍵 ID
        private_key: PEM 形式の秘密鍵文字列
        client_email: SA のメールアドレス (e.g., "sa-name@project.iam.gserviceaccount.com")
        client_id: OAuth 2.0 client ID
        auth_uri: 固定値 "https://accounts.google.com/o/oauth2/auth"
        token_uri: 固定値 "https://oauth2.googleapis.com/token"
        auth_provider_x509_cert_url: SA 認証局 URL
        client_x509_cert_url: SA 公開鍵 URL
        subject: Optional. impersonate 対象の user email (None = 非impersonation)
    """

    type: str
    project_id: str
    private_key_id: str
    private_key: str
    client_email: str
    client_id: str
    auth_uri: str
    token_uri: str
    auth_provider_x509_cert_url: str
    client_x509_cert_url: str
    subject: str | None


__all__ = ["ServiceAccountCredentials"]

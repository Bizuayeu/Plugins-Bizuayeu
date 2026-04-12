#!/usr/bin/env python3
"""
GoogleServiceAccountProvider
============================

ServiceAccountProviderProtocol の Google 実装。

責務:
- Service Account JSON key ファイルの load / validate
- impersonation: subject (impersonate 対象 user email) を設定した新 credentials を返す
  (既存 credentials は immutable、新しい dict を返す)
"""

import json
from pathlib import Path
from typing import Final, List, Tuple

from domain.exceptions import AuthenticationError, CredentialsNotFoundError
from domain.types.service_account import ServiceAccountCredentials

_REQUIRED_FIELDS: Final[Tuple[str, ...]] = (
    "type",
    "project_id",
    "private_key_id",
    "private_key",
    "client_email",
    "client_id",
    "auth_uri",
    "token_uri",
    "auth_provider_x509_cert_url",
    "client_x509_cert_url",
)


class GoogleServiceAccountProvider:
    """Service Account JSON key の load/impersonate 実装"""

    def load_service_account(self, key_path: str) -> ServiceAccountCredentials:
        """
        Service Account JSON key ファイルをロード。

        Args:
            key_path: SA JSON ファイルパス

        Returns:
            ServiceAccountCredentials (subject=None で初期化)

        Raises:
            CredentialsNotFoundError: ファイルが存在しない
            AuthenticationError: JSON parse エラー、必須フィールド欠落
        """
        path = Path(key_path)
        if not path.exists():
            raise CredentialsNotFoundError(
                f"service account key file not found: {key_path}"
            )
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            raise AuthenticationError(
                f"failed to parse service account key: {e}"
            ) from e

        missing = [f for f in _REQUIRED_FIELDS if f not in raw]
        if missing:
            raise AuthenticationError(
                f"service account key missing required fields: {missing}"
            )

        return {
            "type": raw["type"],
            "project_id": raw["project_id"],
            "private_key_id": raw["private_key_id"],
            "private_key": raw["private_key"],
            "client_email": raw["client_email"],
            "client_id": raw["client_id"],
            "auth_uri": raw["auth_uri"],
            "token_uri": raw["token_uri"],
            "auth_provider_x509_cert_url": raw["auth_provider_x509_cert_url"],
            "client_x509_cert_url": raw["client_x509_cert_url"],
            "subject": None,
        }

    def impersonate(
        self,
        credentials: ServiceAccountCredentials,
        subject_email: str,
        scopes: List[str],
    ) -> ServiceAccountCredentials:
        """
        subject を差し替えた新 credentials を返す (immutable)。

        Args:
            credentials: 元 credentials
            subject_email: impersonate 対象 user email
            scopes: 要求スコープ (現状は signature 保持のためのみ、client 生成時に使用)

        Returns:
            subject が更新された新 credentials
        """
        return {**credentials, "subject": subject_email}


__all__ = ["GoogleServiceAccountProvider"]

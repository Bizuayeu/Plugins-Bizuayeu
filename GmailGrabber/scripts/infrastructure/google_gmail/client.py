#!/usr/bin/env python3
"""
GoogleGmailClient
=================

GmailClientProtocol の Google API 実装。

google-api-python-client の gmail service を使用。
- users().messages().list(): ページング付き検索
- users().messages().get(format='raw'): 生MIME取得
- users().labels().list(): ラベル一覧

raw 形式レスポンスは Base64URL-decoded bytes として GmailMessage.raw_mime に格納。
"""

import base64
import binascii
from collections.abc import Iterator
from datetime import datetime, timezone
from typing import Any

from domain.constants import (
    DEFAULT_PAGE_SIZE,
    DEFAULT_SCOPES,
    GMAIL_API_SERVICE_NAME,
    GMAIL_API_VERSION,
    MAX_PAGE_SIZE,
)
from domain.exceptions import GmailApiError, MessageNotFoundError
from domain.types.credentials import OAuthCredentials
from domain.types.message import GmailMessage
from domain.types.service_account import ServiceAccountCredentials


def _to_google_credentials(creds: OAuthCredentials) -> Any:
    """ドメイン中立 OAuthCredentials → google.oauth2.credentials.Credentials"""
    from google.oauth2.credentials import Credentials  # lazy import

    return Credentials(
        token=creds["access_token"],
        refresh_token=creds.get("refresh_token"),
        token_uri=creds["token_uri"],
        client_id=creds["client_id"],
        client_secret=creds["client_secret"],
        scopes=creds["scopes"],
    )


def _to_google_service_account_credentials(
    creds: ServiceAccountCredentials, scopes: list[str]
) -> Any:
    """
    ドメイン中立 ServiceAccountCredentials → google.oauth2.service_account.Credentials

    subject が指定されていれば .with_subject() で impersonation credentials を返す。
    from_service_account_info には subject を渡せないため、dict から事前に除去する。
    """
    from google.oauth2 import service_account  # lazy import

    sa_dict = {k: v for k, v in creds.items() if k != "subject"}
    base = service_account.Credentials.from_service_account_info(sa_dict, scopes=scopes)
    subject = creds.get("subject")
    if subject:
        return base.with_subject(subject)
    return base


class GoogleGmailClient:
    """Gmail API v1 クライアント（google-api-python-client ベース）"""

    def __init__(
        self,
        *,
        credentials: OAuthCredentials | None = None,
        service_account_credentials: ServiceAccountCredentials | None = None,
        user_id: str = "me",
        page_size: int = DEFAULT_PAGE_SIZE,
        scopes: list[str] | None = None,
    ) -> None:
        """
        Args:
            credentials: OAuth 2.0 認証情報 (individual user flow)
            service_account_credentials: Service Account 認証情報 (workspace admin flow)
            user_id: Gmail ユーザー ID (通常 "me" で認証ユーザー自身)
            page_size: list API のページサイズ（最大 500）
            scopes: Service Account 経路で必要なスコープ (OAuth 経路では無視)

        Raises:
            ValueError: credentials と service_account_credentials が両方指定、
                または両方 None
        """
        if credentials is None and service_account_credentials is None:
            raise ValueError(
                "either credentials or service_account_credentials is required"
            )
        if credentials is not None and service_account_credentials is not None:
            raise ValueError(
                "credentials and service_account_credentials are mutually exclusive"
            )

        self._credentials = credentials
        self._service_account_credentials = service_account_credentials
        self._user_id = user_id
        self._page_size = min(page_size, MAX_PAGE_SIZE)
        self._scopes = scopes if scopes is not None else list(DEFAULT_SCOPES)
        self._service = self._build_service()

    def list_message_ids(
        self, query: str, max_results: int | None = None
    ) -> Iterator[str]:
        """
        検索クエリに一致するメッセージIDをページング付きで列挙。

        Args:
            query: Gmail検索クエリ文字列
            max_results: 取得上限 (None = 無制限)
        """
        try:
            page_token: str | None = None
            yielded = 0
            while True:
                request_kwargs: dict = {
                    "userId": self._user_id,
                    "q": query,
                    "maxResults": self._page_size,
                }
                if page_token:
                    request_kwargs["pageToken"] = page_token

                response = (
                    self._service.users().messages().list(**request_kwargs).execute()
                )
                messages = response.get("messages", [])
                for m in messages:
                    if max_results is not None and yielded >= max_results:
                        return
                    yield m["id"]
                    yielded += 1

                page_token = response.get("nextPageToken")
                if not page_token:
                    return
        except Exception as e:
            raise GmailApiError(f"list_message_ids failed: {e}") from e

    def fetch_message(self, message_id: str) -> GmailMessage:
        """単一メッセージを raw 形式で取得"""
        try:
            response = (
                self._service.users()
                .messages()
                .get(userId=self._user_id, id=message_id, format="raw")
                .execute()
            )
        except Exception as e:
            if "404" in str(e) or "not found" in str(e).lower():
                raise MessageNotFoundError(f"message {message_id} not found") from e
            raise GmailApiError(f"fetch_message({message_id}) failed: {e}") from e

        try:
            raw_b64 = response.get("raw", "")
            raw_mime = base64.urlsafe_b64decode(raw_b64.encode("ascii"))
        except (binascii.Error, UnicodeEncodeError, ValueError) as e:
            raise GmailApiError(f"base64 decode failed for {message_id}: {e}") from e

        internal_ms = int(response.get("internalDate", "0"))
        internal_date = datetime.fromtimestamp(internal_ms / 1000, tz=timezone.utc)

        return {
            "gmail_id": response.get("id", message_id),
            "thread_id": response.get("threadId", ""),
            "label_ids": list(response.get("labelIds", [])),
            "snippet": response.get("snippet", ""),
            "internal_date": internal_date,
            "raw_mime": raw_mime,
            "size_estimate": int(response.get("sizeEstimate", 0)),
        }

    def list_labels(self) -> list[dict]:
        """全ラベル一覧を取得"""
        try:
            response = (
                self._service.users().labels().list(userId=self._user_id).execute()
            )
            return list(response.get("labels", []))
        except Exception as e:
            raise GmailApiError(f"list_labels failed: {e}") from e

    def estimate_count(self, query: str) -> int:
        """
        Gmail API は resultSizeEstimate をレスポンスに含めるが、全ページ取得まで
        正確な値は判明しない。ここでは最初のページのみを見て近似値を返す。
        """
        try:
            response = (
                self._service.users()
                .messages()
                .list(userId=self._user_id, q=query, maxResults=1)
                .execute()
            )
            return int(response.get("resultSizeEstimate", 0))
        except Exception as e:
            raise GmailApiError(f"estimate_count failed: {e}") from e

    # =========================================================================
    # internal
    # =========================================================================

    def _build_service(self) -> Any:
        from googleapiclient.discovery import build  # lazy import

        if self._service_account_credentials is not None:
            google_creds = _to_google_service_account_credentials(
                self._service_account_credentials, self._scopes
            )
        else:
            assert self._credentials is not None
            google_creds = _to_google_credentials(self._credentials)
        return build(
            GMAIL_API_SERVICE_NAME,
            GMAIL_API_VERSION,
            credentials=google_creds,
            cache_discovery=False,
        )


__all__ = ["GoogleGmailClient"]

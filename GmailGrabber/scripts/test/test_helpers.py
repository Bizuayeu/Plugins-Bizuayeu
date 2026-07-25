#!/usr/bin/env python3
"""
Test helpers: Fake implementations of domain protocols.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, Iterator, List, Optional

from domain.types.backup import BackupState
from domain.types.credentials import OAuthCredentials
from domain.types.message import GmailMessage
from domain.types.multi_backup import MultiUserBackupState
from domain.types.service_account import ServiceAccountCredentials


class FakeClock:
    """決定的時刻を返す ClockProtocol 実装"""

    def __init__(self, start: Optional[datetime] = None) -> None:
        self._current = start or datetime(2026, 4, 11, 10, 0, 0, tzinfo=timezone.utc)

    def now(self) -> datetime:
        current = self._current
        self._current += timedelta(seconds=1)
        return current

    def set(self, dt: datetime) -> None:
        self._current = dt


class FakeGmailClient:
    """メモリ上 GmailClientProtocol 実装"""

    def __init__(
        self,
        messages: Optional[List[GmailMessage]] = None,
        labels: Optional[List[dict]] = None,
        fetch_failures: Optional[set[str]] = None,
    ) -> None:
        self._messages: Dict[str, GmailMessage] = {m["gmail_id"]: m for m in (messages or [])}
        self._labels = labels or []
        self._fetch_failures = fetch_failures or set()
        self.list_calls: List[str] = []
        self.fetch_calls: List[str] = []

    def list_message_ids(self, query: str, max_results: Optional[int] = None) -> Iterator[str]:
        self.list_calls.append(query)
        ids = list(self._messages.keys())
        if max_results is not None:
            ids = ids[:max_results]
        yield from ids

    def fetch_message(self, message_id: str) -> GmailMessage:
        self.fetch_calls.append(message_id)
        if message_id in self._fetch_failures:
            raise RuntimeError(f"simulated fetch failure: {message_id}")
        return self._messages[message_id]

    def list_labels(self) -> List[dict]:
        return list(self._labels)

    def estimate_count(self, query: str) -> int:
        return len(self._messages)


class FakeMessageWriter:
    """メモリ上 MessageWriterProtocol 実装"""

    def __init__(self, fail_on: Optional[set[str]] = None) -> None:
        self.written: List[GmailMessage] = []
        self.finalized = False
        self._fail_on = fail_on or set()

    def write(self, message: GmailMessage, output_dir: str) -> str:
        if message["gmail_id"] in self._fail_on:
            raise RuntimeError(f"simulated write failure: {message['gmail_id']}")
        self.written.append(message)
        return f"{output_dir}/{message['gmail_id']}.eml"

    def finalize(self, output_dir: str) -> List[str]:
        self.finalized = True
        return []


class FakeStateRepository:
    """メモリ上 StateRepositoryProtocol 実装"""

    def __init__(self) -> None:
        self._store: Dict[str, BackupState] = {}
        self.save_count = 0

    def load(self, plan_id: str, state_dir: str) -> Optional[BackupState]:
        key = f"{state_dir}::{plan_id}"
        stored = self._store.get(key)
        if stored is None:
            return None
        # Deep copy を返して呼び出し側の変更が影響しないようにする
        return {
            "plan_id": stored["plan_id"],
            "fetched_ids": list(stored["fetched_ids"]),
            "failed_ids": list(stored["failed_ids"]),
            "last_updated": stored["last_updated"],
            "total_estimated": stored["total_estimated"],
        }

    def save(self, state: BackupState, state_dir: str) -> None:
        key = f"{state_dir}::{state['plan_id']}"
        self._store[key] = {
            "plan_id": state["plan_id"],
            "fetched_ids": list(state["fetched_ids"]),
            "failed_ids": list(state["failed_ids"]),
            "last_updated": state["last_updated"],
            "total_estimated": state["total_estimated"],
        }
        self.save_count += 1

    def delete(self, plan_id: str, state_dir: str) -> None:
        key = f"{state_dir}::{plan_id}"
        self._store.pop(key, None)


class FakeCredentialsProvider:
    """メモリ上 CredentialsProviderProtocol 実装"""

    def __init__(
        self,
        stored: Optional[OAuthCredentials] = None,
        interactive_result: Optional[OAuthCredentials] = None,
    ) -> None:
        self._stored = stored
        self._interactive_result = interactive_result or {
            "access_token": "new_access",
            "refresh_token": "new_refresh",
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": "test-client",
            "client_secret": "test-secret",
            "scopes": ["https://www.googleapis.com/auth/gmail.readonly"],
            "expires_at": datetime(2099, 12, 31, tzinfo=timezone.utc),
        }
        self.save_called = False
        self.refresh_called = False
        self.interactive_called = False

    def load(self, token_path: str) -> Optional[OAuthCredentials]:
        return self._stored

    def save(self, credentials: OAuthCredentials, token_path: str) -> None:
        self.save_called = True
        self._stored = credentials

    def authenticate_interactive(
        self, client_secret_path: str, scopes: List[str]
    ) -> OAuthCredentials:
        self.interactive_called = True
        return self._interactive_result

    def refresh(self, credentials: OAuthCredentials) -> OAuthCredentials:
        self.refresh_called = True
        return {
            **credentials,
            "access_token": "refreshed_access",
            "expires_at": datetime(2099, 12, 31, tzinfo=timezone.utc),
        }


def make_gmail_message(
    gmail_id: str,
    internal_date: Optional[datetime] = None,
    raw_mime: bytes = b"From: test@example.com\r\n\r\nbody",
) -> GmailMessage:
    """テスト用 GmailMessage ファクトリ"""
    return {
        "gmail_id": gmail_id,
        "thread_id": gmail_id,
        "label_ids": ["INBOX"],
        "snippet": "Preview",
        "internal_date": internal_date or datetime(2026, 4, 5, 14, 30, 0),
        "raw_mime": raw_mime,
        "size_estimate": len(raw_mime),
    }


def make_message_with_id(
    gmail_id: str,
    message_id_header: str,
    internal_date: Optional[datetime] = None,
    extra_headers: str = "",
) -> GmailMessage:
    """
    Message-ID ヘッダ付き GmailMessage ファクトリ。

    dedup テストで使うために、指定した Message-ID ヘッダを raw_mime に埋め込む。
    """
    raw = (
        f"Message-ID: {message_id_header}\r\n"
        f"From: sender@example.com\r\n"
        f"Subject: test\r\n"
        f"{extra_headers}"
        f"\r\n"
        f"body text"
    ).encode("utf-8")
    return make_gmail_message(gmail_id, internal_date=internal_date, raw_mime=raw)


# =============================================================================
# v0.2.0: Multi-User Fakes
# =============================================================================


class FakeServiceAccountProvider:
    """メモリ上 ServiceAccountProviderProtocol 実装"""

    def __init__(self, loaded: Optional[ServiceAccountCredentials] = None) -> None:
        self._loaded = loaded or {
            "type": "service_account",
            "project_id": "fake-project",
            "private_key_id": "fake-key-id",
            "private_key": "fake-private-key",
            "client_email": "sa@fake-project.iam.gserviceaccount.com",
            "client_id": "1234567890",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": "https://example.com/cert",
            "subject": None,
        }
        self.load_calls: List[str] = []
        self.impersonate_calls: List[str] = []

    def load_service_account(self, key_path: str) -> ServiceAccountCredentials:
        self.load_calls.append(key_path)
        return dict(self._loaded)  # type: ignore[return-value]

    def impersonate(
        self,
        credentials: ServiceAccountCredentials,
        subject_email: str,
        scopes: List[str],
    ) -> ServiceAccountCredentials:
        self.impersonate_calls.append(subject_email)
        return {**credentials, "subject": subject_email}


class FakeGmailClientFactory:
    """メモリ上 GmailClientFactoryProtocol 実装"""

    def __init__(
        self,
        clients_by_user: Optional[Dict[str, "FakeGmailClient"]] = None,
        fail_on_users: Optional[set[str]] = None,
    ) -> None:
        self._clients = clients_by_user or {}
        self._fail_on = fail_on_users or set()
        self.create_calls: List[str] = []

    def create_for_user(self, user_email: str) -> "FakeGmailClient":
        self.create_calls.append(user_email)
        if user_email in self._fail_on:
            raise RuntimeError(f"simulated auth failure for {user_email}")
        if user_email in self._clients:
            return self._clients[user_email]
        return FakeGmailClient(messages=[])


class FakeMultiUserStateRepository:
    """メモリ上 MultiUserStateRepositoryProtocol 実装"""

    def __init__(self) -> None:
        self._store: Dict[str, MultiUserBackupState] = {}
        self.save_count = 0

    def load(self, multi_plan_id: str, state_dir: str) -> Optional[MultiUserBackupState]:
        key = f"{state_dir}::{multi_plan_id}"
        stored = self._store.get(key)
        if stored is None:
            return None
        return self._deep_copy(stored)

    def save(self, state: MultiUserBackupState, state_dir: str) -> None:
        key = f"{state_dir}::{state['multi_plan_id']}"
        self._store[key] = self._deep_copy(state)
        self.save_count += 1

    def delete(self, multi_plan_id: str, state_dir: str) -> None:
        key = f"{state_dir}::{multi_plan_id}"
        self._store.pop(key, None)

    def _deep_copy(self, state: MultiUserBackupState) -> MultiUserBackupState:
        return {
            "multi_plan_id": state["multi_plan_id"],
            "per_user_states": {
                k: {
                    "plan_id": v["plan_id"],
                    "fetched_ids": list(v["fetched_ids"]),
                    "failed_ids": list(v["failed_ids"]),
                    "last_updated": v["last_updated"],
                    "total_estimated": v["total_estimated"],
                }
                for k, v in state["per_user_states"].items()
            },
            "message_id_index": dict(state["message_id_index"]),
            "last_updated": state["last_updated"],
            "started_user_emails": list(state["started_user_emails"]),
            "completed_user_emails": list(state["completed_user_emails"]),
        }

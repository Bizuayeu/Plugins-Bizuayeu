#!/usr/bin/env python3
"""
domain/protocols.py テスト
==========================

Protocol が runtime_checkable として機能すること、Fake が isinstance チェックを
通過することを検証。
"""

from datetime import datetime
from typing import Iterator, List, Optional

import pytest

from domain.protocols import (
    ClockProtocol,
    CredentialsProviderProtocol,
    GmailClientFactoryProtocol,
    GmailClientProtocol,
    MessageWriterProtocol,
    MultiUserStateRepositoryProtocol,
    ServiceAccountProviderProtocol,
    StateRepositoryProtocol,
)
from domain.types.backup import BackupState
from domain.types.credentials import OAuthCredentials
from domain.types.message import GmailMessage
from domain.types.multi_backup import MultiUserBackupState
from domain.types.service_account import ServiceAccountCredentials


# =============================================================================
# Fakes
# =============================================================================


class _FakeClock:
    def now(self) -> datetime:
        return datetime(2026, 4, 11, 10, 0, 0)


class _FakeCredentialsProvider:
    def load(self, token_path: str) -> Optional[OAuthCredentials]:
        return None

    def save(self, credentials: OAuthCredentials, token_path: str) -> None:
        pass

    def authenticate_interactive(
        self, client_secret_path: str, scopes: List[str]
    ) -> OAuthCredentials:
        return {
            "access_token": "fake",
            "refresh_token": None,
            "token_uri": "",
            "client_id": "",
            "client_secret": "",
            "scopes": scopes,
            "expires_at": None,
        }

    def refresh(self, credentials: OAuthCredentials) -> OAuthCredentials:
        return credentials


class _FakeGmailClient:
    def list_message_ids(
        self, query: str, max_results: Optional[int] = None
    ) -> Iterator[str]:
        yield from []

    def fetch_message(self, message_id: str) -> GmailMessage:
        return {
            "gmail_id": message_id,
            "thread_id": message_id,
            "label_ids": [],
            "snippet": "",
            "internal_date": datetime(2026, 4, 1),
            "raw_mime": b"",
            "size_estimate": 0,
        }

    def list_labels(self) -> List[dict]:
        return []

    def estimate_count(self, query: str) -> int:
        return 0


class _FakeMessageWriter:
    def write(self, message: GmailMessage, output_dir: str) -> str:
        return f"{output_dir}/{message['gmail_id']}.eml"

    def finalize(self, output_dir: str) -> List[str]:
        return []


class _FakeStateRepository:
    def load(self, plan_id: str, state_dir: str) -> Optional[BackupState]:
        return None

    def save(self, state: BackupState, state_dir: str) -> None:
        pass

    def delete(self, plan_id: str, state_dir: str) -> None:
        pass


# =============================================================================
# Runtime checkable tests
# =============================================================================


class TestClockProtocol:
    @pytest.mark.unit
    def test_fake_clock_satisfies_protocol(self) -> None:
        clock = _FakeClock()
        assert isinstance(clock, ClockProtocol)


class TestCredentialsProviderProtocol:
    @pytest.mark.unit
    def test_fake_satisfies_protocol(self) -> None:
        provider = _FakeCredentialsProvider()
        assert isinstance(provider, CredentialsProviderProtocol)


class TestGmailClientProtocol:
    @pytest.mark.unit
    def test_fake_satisfies_protocol(self) -> None:
        client = _FakeGmailClient()
        assert isinstance(client, GmailClientProtocol)


class TestMessageWriterProtocol:
    @pytest.mark.unit
    def test_fake_satisfies_protocol(self) -> None:
        writer = _FakeMessageWriter()
        assert isinstance(writer, MessageWriterProtocol)


class TestStateRepositoryProtocol:
    @pytest.mark.unit
    def test_fake_satisfies_protocol(self) -> None:
        repo = _FakeStateRepository()
        assert isinstance(repo, StateRepositoryProtocol)


# =============================================================================
# v0.2.0 Fakes
# =============================================================================


class _FakeServiceAccountProvider:
    def load_service_account(self, key_path: str) -> ServiceAccountCredentials:
        return {
            "type": "service_account",
            "project_id": "p",
            "private_key_id": "k",
            "private_key": "key",
            "client_email": "sa@p.iam.gserviceaccount.com",
            "client_id": "123",
            "auth_uri": "",
            "token_uri": "",
            "auth_provider_x509_cert_url": "",
            "client_x509_cert_url": "",
            "subject": None,
        }

    def impersonate(
        self,
        credentials: ServiceAccountCredentials,
        subject_email: str,
        scopes: List[str],
    ) -> ServiceAccountCredentials:
        return {**credentials, "subject": subject_email}


class _FakeGmailClientFactory:
    def create_for_user(self, user_email: str) -> GmailClientProtocol:
        return _FakeGmailClient()


class _FakeMultiUserStateRepository:
    def load(
        self, multi_plan_id: str, state_dir: str
    ) -> Optional[MultiUserBackupState]:
        return None

    def save(self, state: MultiUserBackupState, state_dir: str) -> None:
        pass

    def delete(self, multi_plan_id: str, state_dir: str) -> None:
        pass


class TestServiceAccountProviderProtocol:
    @pytest.mark.unit
    def test_fake_satisfies_protocol(self) -> None:
        provider = _FakeServiceAccountProvider()
        assert isinstance(provider, ServiceAccountProviderProtocol)


class TestGmailClientFactoryProtocol:
    @pytest.mark.unit
    def test_fake_satisfies_protocol(self) -> None:
        factory = _FakeGmailClientFactory()
        assert isinstance(factory, GmailClientFactoryProtocol)


class TestMultiUserStateRepositoryProtocol:
    @pytest.mark.unit
    def test_fake_satisfies_protocol(self) -> None:
        repo = _FakeMultiUserStateRepository()
        assert isinstance(repo, MultiUserStateRepositoryProtocol)

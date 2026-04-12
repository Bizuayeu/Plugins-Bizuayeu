#!/usr/bin/env python3
"""
infrastructure/google_gmail/gmail_client_factory.py テスト
==========================================================
"""

from typing import Any, List
from unittest.mock import MagicMock

import pytest

from domain.types.service_account import ServiceAccountCredentials
from infrastructure.google_gmail.client import GoogleGmailClient
from infrastructure.google_gmail.gmail_client_factory import GoogleGmailClientFactory


def _fake_sa_credentials() -> ServiceAccountCredentials:
    return {
        "type": "service_account",
        "project_id": "p",
        "private_key_id": "kid",
        "private_key": "key",
        "client_email": "sa@p.iam.gserviceaccount.com",
        "client_id": "123",
        "auth_uri": "",
        "token_uri": "",
        "auth_provider_x509_cert_url": "",
        "client_x509_cert_url": "",
        "subject": None,
    }


class _FakeProvider:
    def __init__(self) -> None:
        self.load_calls: list[str] = []
        self.impersonate_calls: list[str] = []

    def load_service_account(self, key_path: str) -> ServiceAccountCredentials:
        self.load_calls.append(key_path)
        return _fake_sa_credentials()

    def impersonate(
        self,
        credentials: ServiceAccountCredentials,
        subject_email: str,
        scopes: List[str],
    ) -> ServiceAccountCredentials:
        self.impersonate_calls.append(subject_email)
        return {**credentials, "subject": subject_email}


def _mock_gmail_build(monkeypatch: pytest.MonkeyPatch) -> None:
    """googleapiclient.discovery.build と SA credentials 変換をモック化"""
    from infrastructure.google_gmail import client as client_module
    import googleapiclient.discovery

    monkeypatch.setattr(
        client_module,
        "_to_google_service_account_credentials",
        lambda creds, scopes: MagicMock(name="SA-Creds"),
    )
    monkeypatch.setattr(
        googleapiclient.discovery, "build", lambda *a, **k: MagicMock(name="Service")
    )


class TestCreateForUser:
    @pytest.mark.unit
    def test_returns_gmail_client(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _mock_gmail_build(monkeypatch)
        provider = _FakeProvider()
        factory = GoogleGmailClientFactory(
            service_account_key_path="/tmp/sa.json",
            provider=provider,
        )

        client = factory.create_for_user("user@example.com")

        assert isinstance(client, GoogleGmailClient)

    @pytest.mark.unit
    def test_loads_key_once_and_caches(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _mock_gmail_build(monkeypatch)
        provider = _FakeProvider()
        factory = GoogleGmailClientFactory(
            service_account_key_path="/tmp/sa.json",
            provider=provider,
        )

        factory.create_for_user("a@example.com")
        factory.create_for_user("b@example.com")
        factory.create_for_user("c@example.com")

        assert len(provider.load_calls) == 1  # 1回だけロード
        assert len(provider.impersonate_calls) == 3  # user ごとに impersonate

    @pytest.mark.unit
    def test_impersonate_called_with_each_user(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _mock_gmail_build(monkeypatch)
        provider = _FakeProvider()
        factory = GoogleGmailClientFactory(
            service_account_key_path="/tmp/sa.json",
            provider=provider,
        )

        factory.create_for_user("alice@m.com")
        factory.create_for_user("bob@m.com")

        assert provider.impersonate_calls == ["alice@m.com", "bob@m.com"]

    @pytest.mark.unit
    def test_different_users_get_different_clients(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _mock_gmail_build(monkeypatch)
        provider = _FakeProvider()
        factory = GoogleGmailClientFactory(
            service_account_key_path="/tmp/sa.json",
            provider=provider,
        )

        client1 = factory.create_for_user("alice@m.com")
        client2 = factory.create_for_user("bob@m.com")

        assert client1 is not client2
        assert client1._service_account_credentials is not None
        assert client2._service_account_credentials is not None
        assert (
            client1._service_account_credentials["subject"]
            != client2._service_account_credentials["subject"]
        )

    @pytest.mark.unit
    def test_uses_default_scopes_when_not_specified(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from domain.constants import DEFAULT_SCOPES

        _mock_gmail_build(monkeypatch)
        provider = _FakeProvider()
        factory = GoogleGmailClientFactory(
            service_account_key_path="/tmp/sa.json", provider=provider
        )

        assert factory._scopes == list(DEFAULT_SCOPES)

    @pytest.mark.unit
    def test_custom_scopes(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _mock_gmail_build(monkeypatch)
        custom = ["https://www.googleapis.com/auth/gmail.modify"]
        provider = _FakeProvider()
        factory = GoogleGmailClientFactory(
            service_account_key_path="/tmp/sa.json",
            scopes=custom,
            provider=provider,
        )

        assert factory._scopes == custom

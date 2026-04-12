#!/usr/bin/env python3
"""
application/auth/authenticate.py テスト
=======================================
"""

from datetime import datetime, timezone

import pytest

from application.auth.authenticate import AuthenticateUseCase
from domain.types.account import GmailAccount
from domain.types.credentials import OAuthCredentials
from test.test_helpers import FakeClock, FakeCredentialsProvider


def _sample_account() -> GmailAccount:
    return {
        "email": "togami-log@meguru-construction.com",
        "label": "togami-log",
        "credentials_path": "/tmp/cs.json",
        "token_path": "/tmp/tok.json",
    }


def _valid_credentials() -> OAuthCredentials:
    return {
        "access_token": "valid_access",
        "refresh_token": "valid_refresh",
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_id": "test-client",
        "client_secret": "test-secret",
        "scopes": ["https://www.googleapis.com/auth/gmail.readonly"],
        "expires_at": datetime(2099, 12, 31, tzinfo=timezone.utc),
    }


def _expired_credentials_with_refresh() -> OAuthCredentials:
    return {
        "access_token": "expired",
        "refresh_token": "still_valid_refresh",
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_id": "test-client",
        "client_secret": "test-secret",
        "scopes": ["https://www.googleapis.com/auth/gmail.readonly"],
        "expires_at": datetime(2020, 1, 1, tzinfo=timezone.utc),
    }


class TestAuthenticate:
    @pytest.mark.unit
    def test_valid_stored_credentials_returned_without_auth(self) -> None:
        provider = FakeCredentialsProvider(stored=_valid_credentials())
        uc = AuthenticateUseCase(provider, FakeClock())

        result = uc.execute(_sample_account())

        assert result["access_token"] == "valid_access"
        assert provider.interactive_called is False
        assert provider.refresh_called is False

    @pytest.mark.unit
    def test_no_stored_triggers_interactive_auth(self) -> None:
        provider = FakeCredentialsProvider(stored=None)
        uc = AuthenticateUseCase(provider, FakeClock())

        result = uc.execute(_sample_account())

        assert provider.interactive_called is True
        assert provider.save_called is True
        assert result["access_token"] == "new_access"

    @pytest.mark.unit
    def test_expired_with_refresh_token_triggers_refresh(self) -> None:
        provider = FakeCredentialsProvider(stored=_expired_credentials_with_refresh())
        uc = AuthenticateUseCase(provider, FakeClock())

        result = uc.execute(_sample_account())

        assert provider.refresh_called is True
        assert provider.interactive_called is False
        assert result["access_token"] == "refreshed_access"
        assert provider.save_called is True

    @pytest.mark.unit
    def test_expired_without_refresh_triggers_interactive(self) -> None:
        expired_no_refresh: OAuthCredentials = {
            "access_token": "expired",
            "refresh_token": None,
            "token_uri": "",
            "client_id": "",
            "client_secret": "",
            "scopes": [],
            "expires_at": datetime(2020, 1, 1, tzinfo=timezone.utc),
        }
        provider = FakeCredentialsProvider(stored=expired_no_refresh)
        uc = AuthenticateUseCase(provider, FakeClock())

        result = uc.execute(_sample_account())

        assert provider.interactive_called is True
        assert result["access_token"] == "new_access"

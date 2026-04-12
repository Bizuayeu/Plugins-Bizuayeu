#!/usr/bin/env python3
"""
infrastructure/google_gmail/oauth_provider.py テスト
====================================================

load / save / refresh の JSON roundtrip とエラー処理。
authenticate_interactive は実際にブラウザを開くため、このテストスイートでは
扱わない（E2Eテストで手動検証）。
"""

from datetime import datetime, timezone
from pathlib import Path

import pytest

from domain.exceptions import CredentialsNotFoundError
from domain.types.credentials import OAuthCredentials
from infrastructure.google_gmail.oauth_provider import GoogleOAuthCredentialsProvider


def _sample_credentials() -> OAuthCredentials:
    return {
        "access_token": "ya29.sample",
        "refresh_token": "1//sample_refresh",
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_id": "123.apps.googleusercontent.com",
        "client_secret": "GOCSPX-sample",
        "scopes": ["https://www.googleapis.com/auth/gmail.readonly"],
        "expires_at": datetime(2099, 12, 31, 23, 59, tzinfo=timezone.utc),
    }


class TestLoad:
    @pytest.mark.integration
    def test_nonexistent_returns_none(self, tmp_path: Path) -> None:
        provider = GoogleOAuthCredentialsProvider()
        result = provider.load(str(tmp_path / "missing.json"))
        assert result is None

    @pytest.mark.integration
    def test_load_after_save_roundtrip(self, tmp_path: Path) -> None:
        provider = GoogleOAuthCredentialsProvider()
        creds = _sample_credentials()
        token_path = str(tmp_path / "token.json")

        provider.save(creds, token_path)
        loaded = provider.load(token_path)

        assert loaded is not None
        assert loaded["access_token"] == creds["access_token"]
        assert loaded["refresh_token"] == creds["refresh_token"]
        assert loaded["scopes"] == creds["scopes"]
        assert loaded["expires_at"] == creds["expires_at"]


class TestSave:
    @pytest.mark.integration
    def test_creates_parent_dir(self, tmp_path: Path) -> None:
        provider = GoogleOAuthCredentialsProvider()
        nested = tmp_path / "nested" / "dir" / "token.json"

        provider.save(_sample_credentials(), str(nested))

        assert nested.exists()

    @pytest.mark.integration
    def test_null_refresh_token_handled(self, tmp_path: Path) -> None:
        provider = GoogleOAuthCredentialsProvider()
        creds = {**_sample_credentials(), "refresh_token": None}
        path = str(tmp_path / "tok.json")

        provider.save(creds, path)  # type: ignore[arg-type]
        loaded = provider.load(path)

        assert loaded is not None
        assert loaded["refresh_token"] is None

    @pytest.mark.integration
    def test_null_expires_at_handled(self, tmp_path: Path) -> None:
        provider = GoogleOAuthCredentialsProvider()
        creds = {**_sample_credentials(), "expires_at": None}
        path = str(tmp_path / "tok.json")

        provider.save(creds, path)  # type: ignore[arg-type]
        loaded = provider.load(path)

        assert loaded is not None
        assert loaded["expires_at"] is None


class TestAuthenticateInteractive:
    @pytest.mark.unit
    def test_missing_client_secret_raises(self, tmp_path: Path) -> None:
        provider = GoogleOAuthCredentialsProvider()
        with pytest.raises(CredentialsNotFoundError):
            provider.authenticate_interactive(
                str(tmp_path / "missing.json"),
                ["https://www.googleapis.com/auth/gmail.readonly"],
            )

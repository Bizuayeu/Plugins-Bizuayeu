#!/usr/bin/env python3
"""
domain/types/credentials.py テスト
==================================

OAuthCredentials TypedDict のフィールド検証。
"""

from datetime import datetime, timezone
from typing import get_type_hints

import pytest

from domain.types.credentials import OAuthCredentials


class TestOAuthCredentials:
    """OAuthCredentials TypedDict のテスト"""

    @pytest.mark.unit
    def test_has_access_token_field(self) -> None:
        hints = get_type_hints(OAuthCredentials)
        assert "access_token" in hints

    @pytest.mark.unit
    def test_has_refresh_token_field(self) -> None:
        hints = get_type_hints(OAuthCredentials)
        assert "refresh_token" in hints

    @pytest.mark.unit
    def test_has_token_uri_field(self) -> None:
        hints = get_type_hints(OAuthCredentials)
        assert "token_uri" in hints

    @pytest.mark.unit
    def test_has_client_id_field(self) -> None:
        hints = get_type_hints(OAuthCredentials)
        assert "client_id" in hints

    @pytest.mark.unit
    def test_has_client_secret_field(self) -> None:
        hints = get_type_hints(OAuthCredentials)
        assert "client_secret" in hints

    @pytest.mark.unit
    def test_has_scopes_field(self) -> None:
        hints = get_type_hints(OAuthCredentials)
        assert "scopes" in hints

    @pytest.mark.unit
    def test_has_expires_at_field(self) -> None:
        hints = get_type_hints(OAuthCredentials)
        assert "expires_at" in hints

    @pytest.mark.unit
    def test_can_construct_full_credentials(self) -> None:
        creds: OAuthCredentials = {
            "access_token": "ya29.xxx",
            "refresh_token": "1//yyy",
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": "abc.apps.googleusercontent.com",
            "client_secret": "GOCSPX-zzz",
            "scopes": ["https://www.googleapis.com/auth/gmail.readonly"],
            "expires_at": datetime(2026, 4, 11, 15, 0, tzinfo=timezone.utc),
        }
        assert creds["access_token"] == "ya29.xxx"
        assert creds["scopes"] == ["https://www.googleapis.com/auth/gmail.readonly"]

    @pytest.mark.unit
    def test_refresh_token_can_be_none_for_one_shot_auth(self) -> None:
        """refresh_token なしの一回限り認証も許容"""
        creds: OAuthCredentials = {
            "access_token": "ya29.xxx",
            "refresh_token": None,
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": "abc",
            "client_secret": "zzz",
            "scopes": [],
            "expires_at": None,
        }
        assert creds["refresh_token"] is None

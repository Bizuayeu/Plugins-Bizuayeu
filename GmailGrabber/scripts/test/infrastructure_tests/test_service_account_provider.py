#!/usr/bin/env python3
"""
infrastructure/google_gmail/service_account_provider.py テスト
==============================================================
"""

import json
from pathlib import Path

import pytest

from domain.exceptions import AuthenticationError, CredentialsNotFoundError
from infrastructure.google_gmail.service_account_provider import (
    GoogleServiceAccountProvider,
)


def _valid_sa_key_dict() -> dict:
    return {
        "type": "service_account",
        "project_id": "test-project",
        "private_key_id": "abc123",
        "private_key": "-----BEGIN PRIVATE KEY-----\nfake\n-----END PRIVATE KEY-----\n",
        "client_email": "sa@test-project.iam.gserviceaccount.com",
        "client_id": "1234567890",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://example.com/cert",
    }


class TestLoad:
    @pytest.mark.integration
    def test_load_valid_key(self, tmp_path: Path) -> None:
        provider = GoogleServiceAccountProvider()
        key_path = tmp_path / "sa_key.json"
        key_path.write_text(json.dumps(_valid_sa_key_dict()), encoding="utf-8")

        creds = provider.load_service_account(str(key_path))

        assert creds["type"] == "service_account"
        assert creds["project_id"] == "test-project"
        assert creds["client_email"] == "sa@test-project.iam.gserviceaccount.com"
        assert creds["subject"] is None

    @pytest.mark.integration
    def test_missing_file_raises(self, tmp_path: Path) -> None:
        provider = GoogleServiceAccountProvider()
        with pytest.raises(CredentialsNotFoundError):
            provider.load_service_account(str(tmp_path / "missing.json"))

    @pytest.mark.integration
    def test_malformed_json_raises(self, tmp_path: Path) -> None:
        provider = GoogleServiceAccountProvider()
        bad_path = tmp_path / "bad.json"
        bad_path.write_text("{not valid json", encoding="utf-8")
        with pytest.raises(AuthenticationError, match="parse"):
            provider.load_service_account(str(bad_path))

    @pytest.mark.integration
    def test_missing_required_field_raises(self, tmp_path: Path) -> None:
        provider = GoogleServiceAccountProvider()
        incomplete = _valid_sa_key_dict()
        del incomplete["private_key"]
        path = tmp_path / "incomplete.json"
        path.write_text(json.dumps(incomplete), encoding="utf-8")

        with pytest.raises(AuthenticationError, match="private_key"):
            provider.load_service_account(str(path))


class TestImpersonate:
    @pytest.mark.unit
    def test_sets_subject(self) -> None:
        provider = GoogleServiceAccountProvider()
        creds = _valid_sa_key_dict()
        creds["subject"] = None
        result = provider.impersonate(creds, "user@example.com", ["scope1"])  # type: ignore[arg-type]
        assert result["subject"] == "user@example.com"

    @pytest.mark.unit
    def test_original_unchanged(self) -> None:
        """immutability: 元 credentials の subject は変わらない"""
        provider = GoogleServiceAccountProvider()
        original = _valid_sa_key_dict()
        original["subject"] = None
        _ = provider.impersonate(original, "user@example.com", [])  # type: ignore[arg-type]
        assert original["subject"] is None

    @pytest.mark.unit
    def test_can_override_subject(self) -> None:
        provider = GoogleServiceAccountProvider()
        creds = _valid_sa_key_dict()
        creds["subject"] = "old@example.com"
        result = provider.impersonate(creds, "new@example.com", [])  # type: ignore[arg-type]
        assert result["subject"] == "new@example.com"

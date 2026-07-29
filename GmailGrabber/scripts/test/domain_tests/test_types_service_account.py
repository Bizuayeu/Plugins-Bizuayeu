#!/usr/bin/env python3
"""
domain/types/service_account.py テスト
======================================
"""

from typing import get_type_hints

import pytest

from domain.types.service_account import ServiceAccountCredentials


class TestServiceAccountCredentials:
    @pytest.mark.unit
    def test_has_all_google_sa_fields(self) -> None:
        hints = get_type_hints(ServiceAccountCredentials)
        required = [
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
            "subject",
        ]
        for field in required:
            assert field in hints, f"missing field: {field}"

    @pytest.mark.unit
    def test_subject_is_optional(self) -> None:
        """impersonation なしの SA credentials 構築"""
        creds: ServiceAccountCredentials = {
            "type": "service_account",
            "project_id": "test-project",
            "private_key_id": "key-id",
            "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
            "client_email": "sa@test-project.iam.gserviceaccount.com",
            "client_id": "123",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": "https://example.com/cert",
            "subject": None,
        }
        assert creds["subject"] is None

    @pytest.mark.unit
    def test_can_construct_with_impersonation(self) -> None:
        creds: ServiceAccountCredentials = {
            "type": "service_account",
            "project_id": "test-project",
            "private_key_id": "key-id",
            "private_key": "key",
            "client_email": "sa@test-project.iam.gserviceaccount.com",
            "client_id": "123",
            "auth_uri": "",
            "token_uri": "",
            "auth_provider_x509_cert_url": "",
            "client_x509_cert_url": "",
            "subject": "user@meguru-construction.example.jp",
        }
        assert creds["subject"] == "user@meguru-construction.example.jp"

    @pytest.mark.unit
    def test_type_field_is_service_account(self) -> None:
        """type は "service_account" 固定の規約"""
        creds: ServiceAccountCredentials = {
            "type": "service_account",
            "project_id": "",
            "private_key_id": "",
            "private_key": "",
            "client_email": "",
            "client_id": "",
            "auth_uri": "",
            "token_uri": "",
            "auth_provider_x509_cert_url": "",
            "client_x509_cert_url": "",
            "subject": None,
        }
        assert creds["type"] == "service_account"

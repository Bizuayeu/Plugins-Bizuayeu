#!/usr/bin/env python3
"""
domain/types/account.py テスト
==============================

GmailAccount TypedDict のフィールド検証。
"""

from typing import get_type_hints

import pytest

from domain.types.account import GmailAccount


class TestGmailAccount:
    """GmailAccount TypedDict のテスト"""

    @pytest.mark.unit
    def test_has_email_field(self) -> None:
        hints = get_type_hints(GmailAccount)
        assert "email" in hints
        assert hints["email"] is str

    @pytest.mark.unit
    def test_has_label_field(self) -> None:
        hints = get_type_hints(GmailAccount)
        assert "label" in hints
        assert hints["label"] is str

    @pytest.mark.unit
    def test_has_credentials_path_field(self) -> None:
        hints = get_type_hints(GmailAccount)
        assert "credentials_path" in hints
        assert hints["credentials_path"] is str

    @pytest.mark.unit
    def test_has_token_path_field(self) -> None:
        hints = get_type_hints(GmailAccount)
        assert "token_path" in hints
        assert hints["token_path"] is str

    @pytest.mark.unit
    def test_can_construct_togami_log_account(self) -> None:
        """実運用する togami-log@ アカウント構築ケース"""
        acc: GmailAccount = {
            "email": "togami-log@meguru-construction.com",
            "label": "togami-log",
            "credentials_path": "/home/user/.gmailgrabber/client_secret.json",
            "token_path": "/home/user/.gmailgrabber/token_togami-log.json",
        }
        assert acc["email"] == "togami-log@meguru-construction.com"
        assert acc["label"] == "togami-log"

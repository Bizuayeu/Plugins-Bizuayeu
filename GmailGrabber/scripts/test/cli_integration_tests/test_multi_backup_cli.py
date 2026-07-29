#!/usr/bin/env python3
"""
interfaces/multi_backup_cli.py テスト
=====================================

argparse と _load_users のユニットテスト。
実際の Google API 呼び出しは含めない (Phase 8 の factory/client テストで対応済み)。
"""

from pathlib import Path

import pytest

from interfaces.multi_backup_cli import _build_accounts, _build_parser, _load_users


class TestArgParse:
    @pytest.mark.unit
    def test_requires_service_account_key(self) -> None:
        parser = _build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(
                [
                    "--impersonate-users",
                    "a@m.com",
                    "--output-dir",
                    "/tmp",
                ]
            )

    @pytest.mark.unit
    def test_requires_impersonate_users_xor_file(self) -> None:
        parser = _build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(
                [
                    "--service-account-key",
                    "/tmp/sa.json",
                    "--output-dir",
                    "/tmp",
                ]
            )

    @pytest.mark.unit
    def test_users_and_file_mutually_exclusive(self) -> None:
        parser = _build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(
                [
                    "--service-account-key",
                    "/tmp/sa.json",
                    "--impersonate-users",
                    "a@m.com",
                    "--impersonate-users-file",
                    "/tmp/users.txt",
                    "--output-dir",
                    "/tmp",
                ]
            )

    @pytest.mark.unit
    def test_format_defaults_to_eml(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(
            [
                "--service-account-key",
                "/tmp/sa.json",
                "--impersonate-users",
                "a@m.com",
                "--output-dir",
                "/tmp",
            ]
        )
        assert args.format == "eml"

    @pytest.mark.unit
    def test_resume_defaults_to_true(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(
            [
                "--service-account-key",
                "/tmp/sa.json",
                "--impersonate-users",
                "a@m.com",
                "--output-dir",
                "/tmp",
            ]
        )
        assert args.resume is True

    @pytest.mark.unit
    def test_no_resume_flag(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(
            [
                "--service-account-key",
                "/tmp/sa.json",
                "--impersonate-users",
                "a@m.com",
                "--output-dir",
                "/tmp",
                "--no-resume",
            ]
        )
        assert args.resume is False


class TestLoadUsers:
    @pytest.mark.unit
    def test_load_users_from_comma_string(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(
            [
                "--service-account-key",
                "/tmp/sa.json",
                "--impersonate-users",
                "a@m.com, b@m.com , c@m.com",
                "--output-dir",
                "/tmp",
            ]
        )
        users = _load_users(args)
        assert users == ["a@m.com", "b@m.com", "c@m.com"]

    @pytest.mark.integration
    def test_load_users_from_file(self, tmp_path: Path) -> None:
        users_file = tmp_path / "users.txt"
        users_file.write_text(
            "alice@m.com\n# comment\nbob@m.com\n\ncarol@m.com\n",
            encoding="utf-8",
        )
        parser = _build_parser()
        args = parser.parse_args(
            [
                "--service-account-key",
                "/tmp/sa.json",
                "--impersonate-users-file",
                str(users_file),
                "--output-dir",
                "/tmp",
            ]
        )
        users = _load_users(args)
        assert users == ["alice@m.com", "bob@m.com", "carol@m.com"]


class TestBuildAccounts:
    @pytest.mark.unit
    def test_build_accounts_from_emails(self, tmp_path: Path) -> None:
        emails = ["alice@meguru.example.jp", "bob@meguru.example.jp"]
        accounts = _build_accounts(emails, tmp_path)

        assert len(accounts) == 2
        assert accounts[0]["email"] == "alice@meguru.example.jp"
        assert accounts[0]["label"] == "alice"
        assert accounts[0]["token_path"] == str(tmp_path / "token_alice.json")
        assert accounts[1]["email"] == "bob@meguru.example.jp"
        assert accounts[1]["label"] == "bob"

    @pytest.mark.unit
    def test_sa_flow_has_empty_credentials_path(self, tmp_path: Path) -> None:
        """Service Account flow では credentials_path は未使用 (空)"""
        accounts = _build_accounts(["a@m.com"], tmp_path)
        assert accounts[0]["credentials_path"] == ""

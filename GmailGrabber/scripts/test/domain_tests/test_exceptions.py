#!/usr/bin/env python3
"""
domain/exceptions.py テスト
===========================
"""

import pytest

from domain.exceptions import (
    AuthenticationError,
    CredentialsNotFoundError,
    ExportError,
    GmailApiError,
    GmailGrabberError,
    InvalidBackupPlanError,
    MessageNotFoundError,
    QueryBuildError,
    StateRepositoryError,
)


class TestExceptionHierarchy:
    """全例外が GmailGrabberError を継承していることを保証"""

    @pytest.mark.unit
    def test_authentication_error_is_gmailgrabber_error(self) -> None:
        assert issubclass(AuthenticationError, GmailGrabberError)

    @pytest.mark.unit
    def test_credentials_not_found_is_gmailgrabber_error(self) -> None:
        assert issubclass(CredentialsNotFoundError, GmailGrabberError)

    @pytest.mark.unit
    def test_gmail_api_error_is_gmailgrabber_error(self) -> None:
        assert issubclass(GmailApiError, GmailGrabberError)

    @pytest.mark.unit
    def test_message_not_found_is_gmail_api_error(self) -> None:
        """MessageNotFoundError は GmailApiError のサブクラス"""
        assert issubclass(MessageNotFoundError, GmailApiError)
        assert issubclass(MessageNotFoundError, GmailGrabberError)

    @pytest.mark.unit
    def test_query_build_error_is_gmailgrabber_error(self) -> None:
        assert issubclass(QueryBuildError, GmailGrabberError)

    @pytest.mark.unit
    def test_export_error_is_gmailgrabber_error(self) -> None:
        assert issubclass(ExportError, GmailGrabberError)

    @pytest.mark.unit
    def test_state_repo_error_is_gmailgrabber_error(self) -> None:
        assert issubclass(StateRepositoryError, GmailGrabberError)

    @pytest.mark.unit
    def test_invalid_backup_plan_is_gmailgrabber_error(self) -> None:
        assert issubclass(InvalidBackupPlanError, GmailGrabberError)


class TestExceptionUsage:
    """例外は通常のPython例外と同様に使えること"""

    @pytest.mark.unit
    def test_can_raise_and_catch_gmailgrabber_error(self) -> None:
        with pytest.raises(GmailGrabberError):
            raise GmailGrabberError("test")

    @pytest.mark.unit
    def test_can_catch_specific_as_base(self) -> None:
        """サブクラス例外を基底クラスでキャッチ可能"""
        with pytest.raises(GmailGrabberError):
            raise AuthenticationError("auth failed")

    @pytest.mark.unit
    def test_error_message_preserved(self) -> None:
        err = ExportError("cannot write file: disk full")
        assert "disk full" in str(err)

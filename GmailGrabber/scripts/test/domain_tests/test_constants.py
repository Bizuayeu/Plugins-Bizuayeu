#!/usr/bin/env python3
"""
domain/constants.py テスト
==========================
"""

import pytest

from domain.constants import (
    DEFAULT_MAX_RETRIES,
    DEFAULT_PAGE_SIZE,
    DEFAULT_SCOPES,
    GMAIL_API_SERVICE_NAME,
    GMAIL_API_VERSION,
    GMAIL_QUERY_DATE_FORMAT,
    GMAIL_READONLY_SCOPE,
    MAX_PAGE_SIZE,
    OUTPUT_FORMAT_EML,
    OUTPUT_FORMAT_MBOX,
    VALID_OUTPUT_FORMATS,
)


class TestGmailScopes:
    @pytest.mark.unit
    def test_readonly_scope_url_format(self) -> None:
        assert GMAIL_READONLY_SCOPE.startswith("https://")
        assert "gmail.readonly" in GMAIL_READONLY_SCOPE

    @pytest.mark.unit
    def test_default_scopes_contains_readonly(self) -> None:
        assert GMAIL_READONLY_SCOPE in DEFAULT_SCOPES


class TestGmailApiVersion:
    @pytest.mark.unit
    def test_service_name_is_gmail(self) -> None:
        assert GMAIL_API_SERVICE_NAME == "gmail"

    @pytest.mark.unit
    def test_version_is_v1(self) -> None:
        assert GMAIL_API_VERSION == "v1"


class TestPaging:
    @pytest.mark.unit
    def test_default_page_size_positive(self) -> None:
        assert DEFAULT_PAGE_SIZE > 0

    @pytest.mark.unit
    def test_default_page_size_under_max(self) -> None:
        assert DEFAULT_PAGE_SIZE <= MAX_PAGE_SIZE

    @pytest.mark.unit
    def test_max_page_size_is_500(self) -> None:
        """Gmail API の上限"""
        assert MAX_PAGE_SIZE == 500


class TestOutputFormats:
    @pytest.mark.unit
    def test_eml_format_constant(self) -> None:
        assert OUTPUT_FORMAT_EML == "eml"

    @pytest.mark.unit
    def test_mbox_format_constant(self) -> None:
        assert OUTPUT_FORMAT_MBOX == "mbox"

    @pytest.mark.unit
    def test_valid_formats_contains_both(self) -> None:
        assert OUTPUT_FORMAT_EML in VALID_OUTPUT_FORMATS
        assert OUTPUT_FORMAT_MBOX in VALID_OUTPUT_FORMATS


class TestRetry:
    @pytest.mark.unit
    def test_max_retries_reasonable(self) -> None:
        assert DEFAULT_MAX_RETRIES >= 1
        assert DEFAULT_MAX_RETRIES <= 10


class TestGmailQueryDateFormat:
    @pytest.mark.unit
    def test_format_is_gmail_spec(self) -> None:
        """Gmail検索仕様: YYYY/MM/DD"""
        assert GMAIL_QUERY_DATE_FORMAT == "%Y/%m/%d"

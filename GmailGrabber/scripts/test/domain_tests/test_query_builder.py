#!/usr/bin/env python3
"""
domain/query_builder.py テスト
==============================

build_gmail_query 純関数の動作検証 + property-based tests。
"""

from datetime import date

import pytest
from hypothesis import given
from hypothesis import strategies as st

from domain.exceptions import QueryBuildError
from domain.query_builder import build_gmail_query
from domain.types.query import SearchQuery


def _empty_query() -> SearchQuery:
    return {
        "from_addr": None,
        "to_addr": None,
        "subject": None,
        "label": None,
        "date_range": None,
        "has_attachment": None,
        "raw_query": None,
    }


# =============================================================================
# Empty / Raw query
# =============================================================================


class TestEmptyQuery:
    @pytest.mark.unit
    def test_all_none_returns_empty_string(self) -> None:
        q = _empty_query()
        assert build_gmail_query(q) == ""


class TestRawQuery:
    @pytest.mark.unit
    def test_raw_query_overrides_other_fields(self) -> None:
        q: SearchQuery = {
            **_empty_query(),
            "from_addr": "ignored@example.com",
            "raw_query": "from:test@example.com has:attachment",
        }
        assert build_gmail_query(q) == "from:test@example.com has:attachment"

    @pytest.mark.unit
    def test_raw_query_trimmed(self) -> None:
        q: SearchQuery = {**_empty_query(), "raw_query": "  from:x@y.com  "}
        assert build_gmail_query(q) == "from:x@y.com"

    @pytest.mark.unit
    def test_empty_raw_query_falls_through(self) -> None:
        """raw_query が空文字列/空白のみなら無視して通常フィールドを見る"""
        q: SearchQuery = {
            **_empty_query(),
            "from_addr": "a@b.com",
            "raw_query": "   ",
        }
        assert build_gmail_query(q) == "from:a@b.com"


# =============================================================================
# Individual fields
# =============================================================================


class TestFromAddr:
    @pytest.mark.unit
    def test_from_addr_generates_from_prefix(self) -> None:
        q: SearchQuery = {**_empty_query(), "from_addr": "togami-log@meguru-construction.com"}
        assert build_gmail_query(q) == "from:togami-log@meguru-construction.com"


class TestToAddr:
    @pytest.mark.unit
    def test_to_addr_generates_to_prefix(self) -> None:
        q: SearchQuery = {**_empty_query(), "to_addr": "team@example.com"}
        assert build_gmail_query(q) == "to:team@example.com"


class TestSubject:
    @pytest.mark.unit
    def test_single_word_subject(self) -> None:
        q: SearchQuery = {**_empty_query(), "subject": "invoice"}
        assert build_gmail_query(q) == "subject:invoice"

    @pytest.mark.unit
    def test_multiword_subject_quoted(self) -> None:
        q: SearchQuery = {**_empty_query(), "subject": "月次報告"}
        assert build_gmail_query(q) == "subject:月次報告"

    @pytest.mark.unit
    def test_subject_with_space_is_quoted(self) -> None:
        q: SearchQuery = {**_empty_query(), "subject": "monthly report"}
        assert build_gmail_query(q) == 'subject:"monthly report"'


class TestLabel:
    @pytest.mark.unit
    def test_label_generates_label_prefix(self) -> None:
        q: SearchQuery = {**_empty_query(), "label": "INBOX"}
        assert build_gmail_query(q) == "label:INBOX"

    @pytest.mark.unit
    def test_label_with_space_is_hyphenated(self) -> None:
        q: SearchQuery = {**_empty_query(), "label": "My Label"}
        assert build_gmail_query(q) == "label:My-Label"


class TestDateRange:
    @pytest.mark.unit
    def test_start_only_generates_after(self) -> None:
        q: SearchQuery = {
            **_empty_query(),
            "date_range": {"start": date(2026, 4, 1), "end": None},
        }
        assert build_gmail_query(q) == "after:2026/04/01"

    @pytest.mark.unit
    def test_end_only_generates_before(self) -> None:
        q: SearchQuery = {
            **_empty_query(),
            "date_range": {"start": None, "end": date(2026, 4, 12)},
        }
        assert build_gmail_query(q) == "before:2026/04/12"

    @pytest.mark.unit
    def test_both_generates_after_before(self) -> None:
        q: SearchQuery = {
            **_empty_query(),
            "date_range": {"start": date(2026, 4, 1), "end": date(2026, 4, 12)},
        }
        assert build_gmail_query(q) == "after:2026/04/01 before:2026/04/12"

    @pytest.mark.unit
    def test_start_after_end_raises_query_build_error(self) -> None:
        q: SearchQuery = {
            **_empty_query(),
            "date_range": {"start": date(2026, 4, 30), "end": date(2026, 4, 1)},
        }
        with pytest.raises(QueryBuildError, match="start.*>.*end"):
            build_gmail_query(q)

    @pytest.mark.unit
    def test_both_none_generates_nothing(self) -> None:
        q: SearchQuery = {
            **_empty_query(),
            "date_range": {"start": None, "end": None},
        }
        assert build_gmail_query(q) == ""


class TestHasAttachment:
    @pytest.mark.unit
    def test_true_generates_has_attachment(self) -> None:
        q: SearchQuery = {**_empty_query(), "has_attachment": True}
        assert build_gmail_query(q) == "has:attachment"

    @pytest.mark.unit
    def test_false_omits_filter(self) -> None:
        q: SearchQuery = {**_empty_query(), "has_attachment": False}
        assert build_gmail_query(q) == ""


# =============================================================================
# Combined
# =============================================================================


class TestCombined:
    @pytest.mark.unit
    def test_typical_monthly_backup_query(self) -> None:
        """実際に使う togami-log@ 月次バックアップのクエリ"""
        q: SearchQuery = {
            "from_addr": None,
            "to_addr": None,
            "subject": None,
            "label": None,
            "date_range": {"start": date(2026, 4, 1), "end": date(2026, 4, 12)},
            "has_attachment": None,
            "raw_query": None,
        }
        result = build_gmail_query(q)
        assert result == "after:2026/04/01 before:2026/04/12"

    @pytest.mark.unit
    def test_from_and_date_range(self) -> None:
        q: SearchQuery = {
            **_empty_query(),
            "from_addr": "a@b.com",
            "date_range": {"start": date(2026, 4, 1), "end": date(2026, 4, 12)},
        }
        assert build_gmail_query(q) == "from:a@b.com after:2026/04/01 before:2026/04/12"


# =============================================================================
# Property-based
# =============================================================================


class TestProperties:
    @pytest.mark.property
    @given(
        email=st.emails(),
    )
    def test_from_addr_always_prefixed(self, email: str) -> None:
        q: SearchQuery = {**_empty_query(), "from_addr": email}
        result = build_gmail_query(q)
        assert result == f"from:{email}"

    @pytest.mark.property
    @given(
        start=st.dates(min_value=date(2000, 1, 1), max_value=date(2099, 12, 31)),
        end=st.dates(min_value=date(2000, 1, 1), max_value=date(2099, 12, 31)),
    )
    def test_date_range_order_invariant(self, start: date, end: date) -> None:
        """start <= end なら必ず成功、start > end なら QueryBuildError"""
        q: SearchQuery = {
            **_empty_query(),
            "date_range": {"start": start, "end": end},
        }
        if start > end:
            with pytest.raises(QueryBuildError):
                build_gmail_query(q)
        else:
            result = build_gmail_query(q)
            assert "after:" in result
            assert "before:" in result

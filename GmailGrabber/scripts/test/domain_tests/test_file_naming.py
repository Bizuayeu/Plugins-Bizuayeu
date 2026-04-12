#!/usr/bin/env python3
"""
domain/file_naming.py テスト
============================
"""

from datetime import datetime

import pytest
from hypothesis import given
from hypothesis import strategies as st

from domain.file_naming import build_plan_id, eml_filename, mbox_filename, sanitize_filename


# =============================================================================
# sanitize_filename
# =============================================================================


class TestSanitizeFilename:
    @pytest.mark.unit
    def test_clean_name_unchanged(self) -> None:
        assert sanitize_filename("invoice_2026_04") == "invoice_2026_04"

    @pytest.mark.unit
    def test_replaces_slash_with_underscore(self) -> None:
        assert sanitize_filename("foo/bar") == "foo_bar"

    @pytest.mark.unit
    def test_replaces_backslash(self) -> None:
        assert sanitize_filename("foo\\bar") == "foo_bar"

    @pytest.mark.unit
    def test_replaces_colon(self) -> None:
        assert sanitize_filename("12:30:45") == "12_30_45"

    @pytest.mark.unit
    def test_replaces_quotes_and_brackets(self) -> None:
        assert sanitize_filename('a"b<c>d|e?f*g') == "a_b_c_d_e_f_g"

    @pytest.mark.unit
    def test_strips_leading_trailing_dots_and_spaces(self) -> None:
        assert sanitize_filename("  .name.  ") == "name"

    @pytest.mark.unit
    def test_empty_becomes_unnamed(self) -> None:
        assert sanitize_filename("") == "unnamed"
        assert sanitize_filename("   ") == "unnamed"

    @pytest.mark.unit
    def test_max_length_truncates(self) -> None:
        long_name = "a" * 300
        assert len(sanitize_filename(long_name, max_length=200)) == 200


# =============================================================================
# eml_filename
# =============================================================================


class TestEmlFilename:
    @pytest.mark.unit
    def test_format_is_timestamp_id_ext(self) -> None:
        result = eml_filename(datetime(2026, 4, 5, 14, 30, 12), "18f3a5b1")
        assert result == "20260405_143012_18f3a5b1.eml"

    @pytest.mark.unit
    def test_always_ends_with_eml(self) -> None:
        result = eml_filename(datetime(2026, 1, 1), "abc")
        assert result.endswith(".eml")

    @pytest.mark.unit
    def test_timestamp_zero_padded(self) -> None:
        """1月1日0時0分0秒 → "20260101_000000_" プレフィックス"""
        result = eml_filename(datetime(2026, 1, 1, 0, 0, 0), "x")
        assert result.startswith("20260101_000000_")


# =============================================================================
# mbox_filename
# =============================================================================


class TestMboxFilename:
    @pytest.mark.unit
    def test_format_is_plan_id_mbox(self) -> None:
        assert mbox_filename("plan_20260411_abc12345") == "plan_20260411_abc12345.mbox"

    @pytest.mark.unit
    def test_sanitizes_plan_id(self) -> None:
        assert mbox_filename("plan/with/slash") == "plan_with_slash.mbox"


# =============================================================================
# build_plan_id
# =============================================================================


class TestBuildPlanId:
    @pytest.mark.unit
    def test_has_plan_prefix(self) -> None:
        pid = build_plan_id("a@b.com", "from:a@b.com", "eml", datetime(2026, 4, 11, 10, 0, 0))
        assert pid.startswith("plan_")

    @pytest.mark.unit
    def test_contains_timestamp(self) -> None:
        pid = build_plan_id("a@b.com", "q", "eml", datetime(2026, 4, 11, 10, 30, 45))
        assert "20260411_103045" in pid

    @pytest.mark.unit
    def test_deterministic_for_same_inputs(self) -> None:
        ts = datetime(2026, 4, 11, 10, 0, 0)
        pid1 = build_plan_id("a@b.com", "q", "eml", ts)
        pid2 = build_plan_id("a@b.com", "q", "eml", ts)
        assert pid1 == pid2

    @pytest.mark.unit
    def test_different_query_yields_different_hash(self) -> None:
        ts = datetime(2026, 4, 11, 10, 0, 0)
        pid1 = build_plan_id("a@b.com", "q1", "eml", ts)
        pid2 = build_plan_id("a@b.com", "q2", "eml", ts)
        assert pid1 != pid2

    @pytest.mark.unit
    def test_different_format_yields_different_hash(self) -> None:
        ts = datetime(2026, 4, 11, 10, 0, 0)
        pid1 = build_plan_id("a@b.com", "q", "eml", ts)
        pid2 = build_plan_id("a@b.com", "q", "mbox", ts)
        assert pid1 != pid2


# =============================================================================
# Property-based
# =============================================================================


class TestSanitizeProperties:
    @pytest.mark.property
    @given(name=st.text(min_size=0, max_size=500))
    def test_never_contains_forbidden_chars(self, name: str) -> None:
        result = sanitize_filename(name)
        forbidden = set('<>:"/\\|?*')
        assert not any(c in forbidden for c in result)

    @pytest.mark.property
    @given(name=st.text(min_size=0, max_size=500))
    def test_never_empty(self, name: str) -> None:
        result = sanitize_filename(name)
        assert len(result) >= 1

    @pytest.mark.property
    @given(name=st.text(min_size=0, max_size=500), max_len=st.integers(min_value=1, max_value=500))
    def test_respects_max_length(self, name: str, max_len: int) -> None:
        result = sanitize_filename(name, max_length=max_len)
        assert len(result) <= max_len

#!/usr/bin/env python3
"""
domain/types/query.py テスト
============================

DateRange / SearchQuery TypedDict のフィールド検証。
"""

from datetime import date
from typing import get_type_hints

import pytest

from domain.types.query import DateRange, SearchQuery

# =============================================================================
# DateRange
# =============================================================================


class TestDateRange:
    """DateRange TypedDict のテスト"""

    @pytest.mark.unit
    def test_has_start_field(self) -> None:
        hints = get_type_hints(DateRange)
        assert "start" in hints

    @pytest.mark.unit
    def test_has_end_field(self) -> None:
        hints = get_type_hints(DateRange)
        assert "end" in hints

    @pytest.mark.unit
    def test_can_construct_with_both_dates(self) -> None:
        dr: DateRange = {"start": date(2026, 4, 1), "end": date(2026, 4, 30)}
        assert dr["start"] == date(2026, 4, 1)
        assert dr["end"] == date(2026, 4, 30)

    @pytest.mark.unit
    def test_start_can_be_none_open_ended(self) -> None:
        """start=None は「下限なし」を意味する"""
        dr: DateRange = {"start": None, "end": date(2026, 4, 30)}
        assert dr["start"] is None
        assert dr["end"] == date(2026, 4, 30)

    @pytest.mark.unit
    def test_end_can_be_none_open_ended(self) -> None:
        """end=None は「上限なし」を意味する"""
        dr: DateRange = {"start": date(2026, 4, 1), "end": None}
        assert dr["start"] == date(2026, 4, 1)
        assert dr["end"] is None

    @pytest.mark.unit
    def test_both_none_allowed(self) -> None:
        """両方None = 無制限（全期間）"""
        dr: DateRange = {"start": None, "end": None}
        assert dr["start"] is None
        assert dr["end"] is None


# =============================================================================
# SearchQuery
# =============================================================================


class TestSearchQuery:
    """SearchQuery TypedDict のテスト"""

    @pytest.mark.unit
    def test_has_from_addr_field(self) -> None:
        hints = get_type_hints(SearchQuery)
        assert "from_addr" in hints

    @pytest.mark.unit
    def test_has_to_addr_field(self) -> None:
        hints = get_type_hints(SearchQuery)
        assert "to_addr" in hints

    @pytest.mark.unit
    def test_has_subject_field(self) -> None:
        hints = get_type_hints(SearchQuery)
        assert "subject" in hints

    @pytest.mark.unit
    def test_has_label_field(self) -> None:
        hints = get_type_hints(SearchQuery)
        assert "label" in hints

    @pytest.mark.unit
    def test_has_date_range_field(self) -> None:
        hints = get_type_hints(SearchQuery)
        assert "date_range" in hints

    @pytest.mark.unit
    def test_has_has_attachment_field(self) -> None:
        hints = get_type_hints(SearchQuery)
        assert "has_attachment" in hints

    @pytest.mark.unit
    def test_has_raw_query_field(self) -> None:
        hints = get_type_hints(SearchQuery)
        assert "raw_query" in hints

    @pytest.mark.unit
    def test_empty_query_all_none(self) -> None:
        """全フィールドNone = 全メール検索を意味する"""
        q: SearchQuery = {
            "from_addr": None,
            "to_addr": None,
            "subject": None,
            "label": None,
            "date_range": None,
            "has_attachment": None,
            "raw_query": None,
        }
        assert q["from_addr"] is None
        assert q["raw_query"] is None

    @pytest.mark.unit
    def test_typical_backup_query(self) -> None:
        """典型的な月次バックアップクエリ: from + date_range"""
        q: SearchQuery = {
            "from_addr": "togami-log@meguru-construction.example.jp",
            "to_addr": None,
            "subject": None,
            "label": None,
            "date_range": {"start": date(2026, 4, 1), "end": date(2026, 4, 12)},
            "has_attachment": None,
            "raw_query": None,
        }
        assert q["from_addr"] == "togami-log@meguru-construction.example.jp"
        assert q["date_range"] is not None
        assert q["date_range"]["start"] == date(2026, 4, 1)

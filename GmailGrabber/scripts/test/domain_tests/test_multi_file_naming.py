#!/usr/bin/env python3
"""
domain/multi_file_naming.py テスト
==================================
"""

from datetime import datetime

import pytest

from domain.multi_file_naming import build_multi_plan_id


class TestBuildMultiPlanId:
    @pytest.mark.unit
    def test_has_multi_plan_prefix(self) -> None:
        ts = datetime(2026, 4, 11, 10, 0, 0)
        pid = build_multi_plan_id(["a@x.com"], "q", "eml", ts)
        assert pid.startswith("multi_plan_")

    @pytest.mark.unit
    def test_contains_timestamp(self) -> None:
        ts = datetime(2026, 4, 11, 10, 30, 45)
        pid = build_multi_plan_id(["a@x.com"], "q", "eml", ts)
        assert "20260411_103045" in pid

    @pytest.mark.unit
    def test_deterministic_for_same_inputs(self) -> None:
        ts = datetime(2026, 4, 11, 10, 0, 0)
        pid1 = build_multi_plan_id(["a@x.com", "b@x.com"], "q", "eml", ts)
        pid2 = build_multi_plan_id(["a@x.com", "b@x.com"], "q", "eml", ts)
        assert pid1 == pid2

    @pytest.mark.unit
    def test_user_list_order_independent(self) -> None:
        """ユーザーリストの順序が違っても同じ plan_id"""
        ts = datetime(2026, 4, 11, 10, 0, 0)
        pid1 = build_multi_plan_id(["a@x.com", "b@x.com"], "q", "eml", ts)
        pid2 = build_multi_plan_id(["b@x.com", "a@x.com"], "q", "eml", ts)
        assert pid1 == pid2

    @pytest.mark.unit
    def test_duplicate_emails_deduplicated(self) -> None:
        """同じ email が複数回入っても結果変わらず"""
        ts = datetime(2026, 4, 11, 10, 0, 0)
        pid1 = build_multi_plan_id(["a@x.com", "a@x.com"], "q", "eml", ts)
        pid2 = build_multi_plan_id(["a@x.com"], "q", "eml", ts)
        assert pid1 == pid2

    @pytest.mark.unit
    def test_different_user_lists_yield_different_hash(self) -> None:
        ts = datetime(2026, 4, 11, 10, 0, 0)
        pid1 = build_multi_plan_id(["a@x.com"], "q", "eml", ts)
        pid2 = build_multi_plan_id(["b@x.com"], "q", "eml", ts)
        assert pid1 != pid2

    @pytest.mark.unit
    def test_different_query_yields_different_hash(self) -> None:
        ts = datetime(2026, 4, 11, 10, 0, 0)
        pid1 = build_multi_plan_id(["a@x.com"], "q1", "eml", ts)
        pid2 = build_multi_plan_id(["a@x.com"], "q2", "eml", ts)
        assert pid1 != pid2

    @pytest.mark.unit
    def test_different_format_yields_different_hash(self) -> None:
        ts = datetime(2026, 4, 11, 10, 0, 0)
        pid1 = build_multi_plan_id(["a@x.com"], "q", "eml", ts)
        pid2 = build_multi_plan_id(["a@x.com"], "q", "mbox", ts)
        assert pid1 != pid2

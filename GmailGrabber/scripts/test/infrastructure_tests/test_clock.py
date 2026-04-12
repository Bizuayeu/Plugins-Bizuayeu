#!/usr/bin/env python3
"""
infrastructure/clock.py テスト
==============================
"""

from datetime import datetime, timezone

import pytest

from infrastructure.clock import SystemClock


class TestSystemClock:
    @pytest.mark.unit
    def test_now_returns_utc_aware_datetime(self) -> None:
        clock = SystemClock()
        now = clock.now()
        assert now.tzinfo is not None
        assert now.utcoffset() == timezone.utc.utcoffset(None)

    @pytest.mark.unit
    def test_subsequent_calls_monotonic(self) -> None:
        clock = SystemClock()
        t1 = clock.now()
        t2 = clock.now()
        assert t2 >= t1

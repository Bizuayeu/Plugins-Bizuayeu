#!/usr/bin/env python3
"""
infrastructure/clock.py テスト
==============================

SystemClock の動作検証。

検証ポイント:
- now() が tz-aware datetime を返す
- ClockProtocol を満たす（structural typing）
- 連続呼び出しで時刻が単調増加
"""

from datetime import datetime, timezone

import pytest

from domain.protocols import ClockProtocol
from infrastructure.clock import SystemClock


class TestSystemClock:
    @pytest.mark.unit
    def test_now_returns_datetime(self) -> None:
        clock = SystemClock()
        result = clock.now()
        assert isinstance(result, datetime)

    @pytest.mark.unit
    def test_now_is_tz_aware(self) -> None:
        """tz-aware（タイムゾーン情報を持つ）"""
        clock = SystemClock()
        result = clock.now()
        assert result.tzinfo is not None

    @pytest.mark.unit
    def test_satisfies_clock_protocol(self) -> None:
        """ClockProtocol を満たす（runtime_checkable）"""
        clock: ClockProtocol = SystemClock()
        assert hasattr(clock, "now")

    @pytest.mark.unit
    def test_now_monotonic(self) -> None:
        """連続呼び出しで時刻が後退しない"""
        clock = SystemClock()
        t1 = clock.now()
        t2 = clock.now()
        assert t2 >= t1

    @pytest.mark.unit
    def test_default_uses_local_timezone(self) -> None:
        """デフォルトはローカル TZ（system timezone）"""
        clock = SystemClock()
        result = clock.now()
        # ローカルタイムゾーンの offset を持つ
        assert result.utcoffset() is not None

    @pytest.mark.unit
    def test_custom_timezone_utc(self) -> None:
        """UTC を明示注入できる"""
        clock = SystemClock(tz=timezone.utc)
        result = clock.now()
        assert result.tzinfo == timezone.utc

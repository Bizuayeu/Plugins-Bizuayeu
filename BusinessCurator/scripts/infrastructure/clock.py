#!/usr/bin/env python3
"""
SystemClock
===========

ClockProtocol の本番実装。

設計意図:
- now() は tz-aware datetime を返す（曖昧性を排除）
- デフォルトはローカル TZ（system timezone）
- テスト時は FakeClock を使用（test_helpers.py）
"""

from datetime import datetime, timezone
from typing import Optional

__all__ = ["SystemClock"]


class SystemClock:
    """
    システム時計（本番用 ClockProtocol 実装）

    Attributes:
        _tz: 注入されたタイムゾーン（None ならローカル）
    """

    def __init__(self, tz: Optional[timezone] = None) -> None:
        """
        Args:
            tz: 使用するタイムゾーン（省略時はローカル TZ）
        """
        self._tz = tz

    def now(self) -> datetime:
        """
        現在時刻を tz-aware で返す

        Returns:
            datetime（tzinfo 必ず存在）
        """
        if self._tz is not None:
            return datetime.now(self._tz)
        # ローカル TZ（astimezone() で system TZ に変換）
        return datetime.now().astimezone()

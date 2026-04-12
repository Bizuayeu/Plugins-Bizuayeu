#!/usr/bin/env python3
"""
SystemClock
===========

ClockProtocol の本番実装。実時刻を UTC aware datetime で返す。
"""

from datetime import datetime, timezone


class SystemClock:
    """システム時刻を UTC aware で返す clock"""

    def now(self) -> datetime:
        return datetime.now(timezone.utc)


__all__ = ["SystemClock"]

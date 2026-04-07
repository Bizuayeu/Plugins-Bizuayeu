#!/usr/bin/env python3
"""
JsonTriageLogRepository
=======================

TriageLogRepositoryProtocol の JSON ファイル実装。

設計意図:
- 日次 1 ファイル: _triage_log_YYYYMMDD.json
- ファイルは JSON 配列（配列の append による追記）
- 既存ファイルへの追記時は読み込み → append → 書き戻し
- atomic write を意識しつつ、シンプルさを優先（ロックは Phase 6 以降）
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, List

from domain.exceptions import TriageError
from domain.types.triage import TriageLogEntry

__all__ = ["JsonTriageLogRepository"]


class JsonTriageLogRepository:
    """
    triage_logs/_triage_log_YYYYMMDD.json への永続化
    """

    def __init__(self, triage_logs_dir: Path) -> None:
        self._dir = triage_logs_dir

    # ------------------------------------------------------------------
    # path
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_date(date: str) -> str:
        """YYYY-MM-DD または YYYYMMDD → YYYYMMDD"""
        compact = date.replace("-", "")
        if len(compact) != 8 or not compact.isdigit():
            raise ValueError(f"invalid date format: {date!r}")
        return compact

    def _path_for_date(self, date_compact: str) -> Path:
        return self._dir / f"_triage_log_{date_compact}.json"

    @staticmethod
    def _extract_date_from_timestamp(timestamp: str) -> str:
        """ISO 8601 timestamp → YYYYMMDD"""
        try:
            dt = datetime.fromisoformat(timestamp)
        except ValueError as e:
            raise TriageError(f"invalid timestamp in log entry: {timestamp!r}") from e
        return dt.strftime("%Y%m%d")

    # ------------------------------------------------------------------
    # append
    # ------------------------------------------------------------------

    def append(self, log_entry: TriageLogEntry) -> None:
        """
        ログエントリを日次ファイルに追記

        Args:
            log_entry: 追記対象

        Raises:
            TriageError: timestamp パース不能、または書き込み失敗
        """
        date_compact = self._extract_date_from_timestamp(log_entry["timestamp"])
        self._dir.mkdir(parents=True, exist_ok=True)
        path = self._path_for_date(date_compact)

        existing: List[Any] = []
        if path.exists():
            existing = json.loads(path.read_text(encoding="utf-8"))

        existing.append(log_entry)
        path.write_text(
            json.dumps(existing, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    # ------------------------------------------------------------------
    # load
    # ------------------------------------------------------------------

    def load_for_date(self, date: str) -> List[TriageLogEntry]:
        """
        指定日のログを取得

        Args:
            date: YYYY-MM-DD または YYYYMMDD

        Returns:
            TriageLogEntry のリスト（時刻順、ファイルなしは空リスト）
        """
        date_compact = self._normalize_date(date)
        path = self._path_for_date(date_compact)
        if not path.exists():
            return []
        data = json.loads(path.read_text(encoding="utf-8"))
        return data  # type: ignore[no-any-return]

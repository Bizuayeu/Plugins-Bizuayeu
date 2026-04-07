#!/usr/bin/env python3
"""
IngestBatchUseCase
==================

メールファイル → RawEntry の一括ingestユースケース。

設計意図:
- EmailParserProtocol.parse_many → ParseEmailUseCase → EntryRepository.save
- 既存エントリは skip（冪等性：再実行で同じ結果）
- パース失敗は IngestError として呼び出し側に伝播（フェイルファスト）
- IngestBatchResult: saved/skipped/failed のサマリーを返す
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

from application.ingest.parse_email import ParseEmailUseCase
from domain.exceptions import IngestError
from domain.protocols import EmailParserProtocol, EntryRepositoryProtocol

__all__ = ["IngestBatchResult", "IngestBatchUseCase"]


@dataclass
class IngestBatchResult:
    """
    Ingest 実行サマリー

    Attributes:
        saved: 新規保存件数
        skipped: 既存と判断され skip した件数
        failed: パース成功後の保存失敗件数（現状は到達しないが将来用）
    """

    saved: int = 0
    skipped: int = 0
    failed: int = 0

    @property
    def total(self) -> int:
        return self.saved + self.skipped + self.failed

    def to_dict(self) -> Dict[str, Any]:
        return {
            "saved": self.saved,
            "skipped": self.skipped,
            "failed": self.failed,
            "total": self.total,
        }


class IngestBatchUseCase:
    """ファイルから RawEntry をバッチ生成するユースケース"""

    def __init__(
        self,
        email_parser: EmailParserProtocol,
        parse_usecase: ParseEmailUseCase,
        entry_repository: EntryRepositoryProtocol,
    ) -> None:
        self._parser = email_parser
        self._parse_uc = parse_usecase
        self._repo = entry_repository

    def execute(self, source: Path) -> IngestBatchResult:
        """
        ソースファイルからエントリを取り込み

        Args:
            source: .eml または .mbox ファイル

        Returns:
            IngestBatchResult

        Raises:
            IngestError: パース失敗（フェイルファスト）
        """
        result = IngestBatchResult()

        try:
            messages = self._parser.parse_many(source)
        except Exception as e:
            raise IngestError(f"failed to parse {source}: {e}") from e

        for msg in messages:
            entry = self._parse_uc.execute(msg)
            if self._repo.exists(entry["id"]):
                result.skipped += 1
                continue
            self._repo.save(entry)
            result.saved += 1

        return result

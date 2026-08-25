#!/usr/bin/env python3
"""
application/ingest/ingest_batch.py テスト
==========================================

IngestBatchUseCase 動作検証。

検証ポイント:
- パーサー → ParseEmailUseCase → EntryRepository.save の流れ
- 同じ入力で2回実行しても結果が同一（冪等性）
- 既存エントリは skip するか上書きするか（明示的選択）
- パース失敗時のエラーハンドリング
- IngestResult: saved/skipped/failed のサマリー
"""

from datetime import datetime
from pathlib import Path

import pytest

from application.ingest.ingest_batch import IngestBatchResult, IngestBatchUseCase
from application.ingest.parse_email import ParseEmailUseCase
from test.test_helpers import (
    FakeEmailParser,
    FakeEntryRepository,
    build_email_message,
)

# =============================================================================
# Helpers
# =============================================================================


def build_usecase(
    messages,
    repo=None,
):  # type: ignore[no-untyped-def]
    parser = FakeEmailParser(many=messages)
    entry_repo = repo or FakeEntryRepository()
    parse_uc = ParseEmailUseCase()
    return (
        IngestBatchUseCase(
            email_parser=parser, parse_usecase=parse_uc, entry_repository=entry_repo
        ),
        parser,
        entry_repo,
    )


# =============================================================================
# 基本動作
# =============================================================================


class TestIngestBatchUseCaseBasic:
    @pytest.mark.unit
    def test_executes_with_no_messages(self) -> None:
        usecase, _, repo = build_usecase(messages=[])
        result = usecase.execute(Path("dummy.mbox"))
        assert isinstance(result, IngestBatchResult)
        assert result.saved == 0
        assert repo.list_all() == []

    @pytest.mark.unit
    def test_saves_single_message(self) -> None:
        msg = build_email_message(message_id="<a@x>")
        usecase, _, repo = build_usecase(messages=[msg])
        result = usecase.execute(Path("dummy.mbox"))
        assert result.saved == 1
        assert len(repo.list_all()) == 1

    @pytest.mark.unit
    def test_saves_multiple_messages(self) -> None:
        msgs = [
            build_email_message(
                message_id=f"<{i}@x>", date=datetime(2026, 4, 7, 14, 30, i)
            )
            for i in range(5)
        ]
        usecase, _, repo = build_usecase(messages=msgs)
        result = usecase.execute(Path("dummy.mbox"))
        assert result.saved == 5
        assert len(repo.list_all()) == 5

    @pytest.mark.unit
    def test_passes_input_path_to_parser(self) -> None:
        usecase, parser, _ = build_usecase(messages=[])
        usecase.execute(Path("foo/bar.mbox"))
        assert parser.parse_many_calls == [Path("foo/bar.mbox")]


# =============================================================================
# 冪等性
# =============================================================================


class TestIngestBatchUseCaseIdempotency:
    """同じ入力で2回実行しても repo の内容が同一"""

    @pytest.mark.unit
    def test_re_execution_keeps_same_count(self) -> None:
        msgs = [
            build_email_message(
                message_id=f"<{i}@x>", date=datetime(2026, 4, 7, 14, 30, i)
            )
            for i in range(3)
        ]
        usecase, _, repo = build_usecase(messages=msgs)
        usecase.execute(Path("dummy.mbox"))
        first = sorted(e["id"] for e in repo.list_all())
        usecase.execute(Path("dummy.mbox"))
        second = sorted(e["id"] for e in repo.list_all())
        assert first == second

    @pytest.mark.unit
    def test_re_execution_reports_skipped(self) -> None:
        """2回目実行では既存分は skipped 扱い"""
        msgs = [build_email_message(message_id="<x@y>")]
        usecase, _, _ = build_usecase(messages=msgs)
        first = usecase.execute(Path("a.mbox"))
        second = usecase.execute(Path("a.mbox"))
        assert first.saved == 1
        assert first.skipped == 0
        assert second.saved == 0
        assert second.skipped == 1


# =============================================================================
# Result サマリ
# =============================================================================


class TestIngestBatchResult:
    @pytest.mark.unit
    def test_total_property(self) -> None:
        result = IngestBatchResult(saved=3, skipped=2, failed=1)
        assert result.total == 6

    @pytest.mark.unit
    def test_to_dict(self) -> None:
        result = IngestBatchResult(saved=3, skipped=2, failed=1)
        d = result.to_dict()
        assert d == {"saved": 3, "skipped": 2, "failed": 1, "total": 6}


# =============================================================================
# パース失敗
# =============================================================================


class TestIngestBatchUseCaseFailure:
    """パース失敗の扱い"""

    @pytest.mark.unit
    def test_parser_exception_is_propagated(self) -> None:
        """parse_many が例外を投げたら IngestError として浮かぶ（フェイルファスト）"""

        class BrokenParser:
            def parse(self, path: Path):  # type: ignore[no-untyped-def]
                raise RuntimeError("dummy")

            def parse_many(self, path: Path):  # type: ignore[no-untyped-def]
                raise RuntimeError("simulated parser failure")

        from domain.exceptions import IngestError

        repo = FakeEntryRepository()
        parse_uc = ParseEmailUseCase()
        usecase = IngestBatchUseCase(
            email_parser=BrokenParser(),  # type: ignore[arg-type]
            parse_usecase=parse_uc,
            entry_repository=repo,
        )
        with pytest.raises(IngestError, match="simulated parser failure"):
            usecase.execute(Path("dummy.mbox"))

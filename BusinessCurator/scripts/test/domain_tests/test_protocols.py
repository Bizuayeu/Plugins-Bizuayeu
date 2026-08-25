#!/usr/bin/env python3
"""
domain/protocols.py テスト
==========================

Protocol 定義の存在とインターフェース契約のテスト。

設計意図:
- Protocol は依存関係逆転（DIP）の要
- application 層は Protocol に依存し、infrastructure 層が実装する
- ここでは「契約が壊れていないか」を runtime_checkable で検証
- 実装の細部は infrastructure_tests で検証

検証対象 Protocol:
- ClockProtocol
- EmailParserProtocol
- EntryRepositoryProtocol
- AliasResolverRepositoryProtocol
- TriageLogRepositoryProtocol
- LLMTriageProtocol
"""

from datetime import datetime
from pathlib import Path

import pytest

from domain.protocols import (
    AliasResolverRepositoryProtocol,
    ClockProtocol,
    EmailParserProtocol,
    EntryRepositoryProtocol,
    LLMTriageProtocol,
    TriageLogRepositoryProtocol,
)
from domain.types.alias import AliasRecord
from domain.types.email import EmailMessage
from domain.types.entry import RawEntry
from domain.types.shard import ShardKind
from domain.types.triage import TriageLogEntry

# =============================================================================
# ClockProtocol
# =============================================================================


class TestClockProtocol:
    """ClockProtocol のテスト"""

    @pytest.mark.unit
    def test_has_now_method(self) -> None:
        """now() メソッドが定義されている"""
        assert hasattr(ClockProtocol, "now")

    @pytest.mark.unit
    def test_fake_implementation_satisfies(self) -> None:
        """偽実装が Protocol を満たす（structural typing）"""

        class FakeClock:
            def now(self) -> datetime:
                return datetime(2026, 4, 7, 14, 30, 22)

        clock: ClockProtocol = FakeClock()
        assert clock.now().year == 2026


# =============================================================================
# EmailParserProtocol
# =============================================================================


class TestEmailParserProtocol:
    """EmailParserProtocol のテスト"""

    @pytest.mark.unit
    def test_has_parse_method(self) -> None:
        """parse(path) メソッドが定義されている"""
        assert hasattr(EmailParserProtocol, "parse")

    @pytest.mark.unit
    def test_has_parse_many_method(self) -> None:
        """parse_many(path) メソッドが定義されている"""
        assert hasattr(EmailParserProtocol, "parse_many")

    @pytest.mark.unit
    def test_fake_implementation_satisfies(self) -> None:
        """偽実装が EmailParserProtocol を満たす"""

        class FakeParser:
            def parse(self, path: Path) -> EmailMessage:
                return {
                    "message_id": "<a@b>",
                    "from_addr": {"name": "", "address": "a@b"},
                    "to_addrs": [],
                    "cc_addrs": [],
                    "subject": "test",
                    "date": datetime(2026, 4, 7),
                    "body_text": "",
                    "body_html": None,
                    "attachments": [],
                    "thread_id": None,
                    "in_reply_to": None,
                    "references": [],
                }

            def parse_many(self, path: Path) -> list[EmailMessage]:
                return [self.parse(path)]

        parser: EmailParserProtocol = FakeParser()
        msg = parser.parse(Path("dummy.eml"))
        assert msg["message_id"] == "<a@b>"


# =============================================================================
# EntryRepositoryProtocol
# =============================================================================


class TestEntryRepositoryProtocol:
    """EntryRepositoryProtocol のテスト"""

    @pytest.mark.unit
    def test_has_save_method(self) -> None:
        """save(entry) メソッド"""
        assert hasattr(EntryRepositoryProtocol, "save")

    @pytest.mark.unit
    def test_has_exists_method(self) -> None:
        """exists(entry_id) メソッド"""
        assert hasattr(EntryRepositoryProtocol, "exists")

    @pytest.mark.unit
    def test_has_load_method(self) -> None:
        """load(entry_id) メソッド"""
        assert hasattr(EntryRepositoryProtocol, "load")

    @pytest.mark.unit
    def test_has_list_all_method(self) -> None:
        """list_all() メソッド"""
        assert hasattr(EntryRepositoryProtocol, "list_all")

    @pytest.mark.unit
    def test_fake_implementation_satisfies(self) -> None:
        """偽実装が満たす"""

        class FakeRepo:
            def __init__(self) -> None:
                self._store: dict[str, RawEntry] = {}

            def save(self, entry: RawEntry) -> None:
                self._store[entry["id"]] = entry

            def exists(self, entry_id: str) -> bool:
                return entry_id in self._store

            def load(self, entry_id: str) -> RawEntry:
                return self._store[entry_id]

            def list_all(self) -> list[RawEntry]:
                return list(self._store.values())

        repo: EntryRepositoryProtocol = FakeRepo()
        assert repo.list_all() == []


# =============================================================================
# AliasResolverRepositoryProtocol
# =============================================================================


class TestAliasResolverRepositoryProtocol:
    """AliasResolverRepositoryProtocol のテスト"""

    @pytest.mark.unit
    def test_has_load_all_method(self) -> None:
        assert hasattr(AliasResolverRepositoryProtocol, "load_all")

    @pytest.mark.unit
    def test_has_save_all_method(self) -> None:
        assert hasattr(AliasResolverRepositoryProtocol, "save_all")

    @pytest.mark.unit
    def test_fake_implementation_satisfies(self) -> None:
        class FakeResolver:
            def __init__(self) -> None:
                self._records: list[AliasRecord] = []

            def load_all(self) -> list[AliasRecord]:
                return list(self._records)

            def save_all(self, records: list[AliasRecord]) -> None:
                self._records = list(records)

        repo: AliasResolverRepositoryProtocol = FakeResolver()
        repo.save_all([])
        assert repo.load_all() == []


# =============================================================================
# TriageLogRepositoryProtocol
# =============================================================================


class TestTriageLogRepositoryProtocol:
    """TriageLogRepositoryProtocol のテスト"""

    @pytest.mark.unit
    def test_has_append_method(self) -> None:
        assert hasattr(TriageLogRepositoryProtocol, "append")

    @pytest.mark.unit
    def test_has_load_for_date_method(self) -> None:
        assert hasattr(TriageLogRepositoryProtocol, "load_for_date")

    @pytest.mark.unit
    def test_fake_implementation_satisfies(self) -> None:
        class FakeLog:
            def __init__(self) -> None:
                self._entries: list[TriageLogEntry] = []

            def append(self, log_entry: TriageLogEntry) -> None:
                self._entries.append(log_entry)

            def load_for_date(self, date: str) -> list[TriageLogEntry]:
                return [e for e in self._entries if e["timestamp"].startswith(date)]

        repo: TriageLogRepositoryProtocol = FakeLog()
        assert repo.load_for_date("2026-04-07") == []


# =============================================================================
# LLMTriageProtocol
# =============================================================================


class TestLLMTriageProtocol:
    """LLMTriageProtocol のテスト"""

    @pytest.mark.unit
    def test_has_classify_method(self) -> None:
        """classify(entry) メソッド"""
        assert hasattr(LLMTriageProtocol, "classify")

    @pytest.mark.unit
    def test_fake_implementation_satisfies(self) -> None:
        """FakeLLMTriageClient パターン"""

        class FakeLLM:
            def __init__(self, response: ShardKind = "knowledge") -> None:
                self.response = response
                self.calls: list[str] = []

            def classify(self, entry: RawEntry) -> ShardKind:
                self.calls.append(entry["id"])
                return self.response

        llm: LLMTriageProtocol = FakeLLM("projects")
        entry: RawEntry = {
            "id": "email_20260407_143022_abc12345",
            "date": "2026-04-07",
            "time": "14:30:22",
            "source_type": "email",
            "from_addr": "a@b",
            "to_addrs": [],
            "cc_addrs": [],
            "subject": "",
            "thread_id": None,
            "attachments": [],
            "tags": [],
            "body": "",
        }
        result = llm.classify(entry)
        assert result == "projects"

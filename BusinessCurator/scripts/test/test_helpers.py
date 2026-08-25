#!/usr/bin/env python3
"""
Test Helpers Module
===================

BusinessCurator用テスト共通ヘルパー。

設計意図:
- Phase 2 では `tmp_path` 使用ゼロを目標とする（純粋なドメイン型でテスト）
- Fake 実装群は Protocol の structural typing を満たすクラス
- Application 層 UseCase に注入することで infrastructure 不在でテスト可能
- データビルダーは TypedDict のデフォルト値生成

提供するもの:
- FakeClock: ClockProtocol 実装
- FakeEntryRepository: EntryRepositoryProtocol 実装（in-memory dict）
- FakeAliasResolverRepository: AliasResolverRepositoryProtocol 実装（in-memory list）
- FakeTriageLogRepository: TriageLogRepositoryProtocol 実装（in-memory list）
- FakeLLMTriageClient: LLMTriageProtocol 実装（dict 駆動の固定応答）
- FakeEmailParser: EmailParserProtocol 実装（事前注入 list 返却）
- build_email_message: EmailMessage デフォルト値ビルダー
- build_raw_entry: RawEntry デフォルト値ビルダー
- build_alias_record: AliasRecord デフォルト値ビルダー
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from domain.exceptions import EntityNotFoundError
from domain.types.alias import AliasRecord
from domain.types.email import EmailMessage
from domain.types.entry import RawEntry
from domain.types.shard import ArchiveStatus, ShardKind
from domain.types.triage import TriageLogEntry

# =============================================================================
# Fake: Clock
# =============================================================================


class FakeClock:
    """
    決定的時刻提供（ClockProtocol 実装）

    テストごとに固定の datetime を返す。
    `advance(seconds)` で時刻を進めることも可能。
    """

    def __init__(self, fixed: datetime) -> None:
        self._current = fixed

    def now(self) -> datetime:
        return self._current

    def advance(self, seconds: float) -> None:
        from datetime import timedelta

        self._current = self._current + timedelta(seconds=seconds)


# =============================================================================
# Fake: EntryRepository
# =============================================================================


class FakeEntryRepository:
    """
    in-memory な EntryRepositoryProtocol 実装

    save 順序を保持し、list_all は登録順で返す。
    """

    def __init__(self) -> None:
        self._store: dict[str, RawEntry] = {}
        self.save_count = 0

    def save(self, entry: RawEntry) -> None:
        self._store[entry["id"]] = entry
        self.save_count += 1

    def exists(self, entry_id: str) -> bool:
        return entry_id in self._store

    def load(self, entry_id: str) -> RawEntry:
        if entry_id not in self._store:
            raise EntityNotFoundError(f"entry not found: {entry_id}")
        return self._store[entry_id]

    def list_all(self) -> list[RawEntry]:
        return list(self._store.values())


# =============================================================================
# Fake: AliasResolverRepository
# =============================================================================


class FakeAliasResolverRepository:
    """
    in-memory な AliasResolverRepositoryProtocol 実装
    """

    def __init__(self, initial: list[AliasRecord] | None = None) -> None:
        self._records: list[AliasRecord] = list(initial) if initial else []
        self.save_count = 0

    def load_all(self) -> list[AliasRecord]:
        return list(self._records)

    def save_all(self, records: list[AliasRecord]) -> None:
        self._records = list(records)
        self.save_count += 1


# =============================================================================
# Fake: TriageLogRepository
# =============================================================================


class FakeTriageLogRepository:
    """
    in-memory な TriageLogRepositoryProtocol 実装
    """

    def __init__(self) -> None:
        self._entries: list[TriageLogEntry] = []

    def append(self, log_entry: TriageLogEntry) -> None:
        self._entries.append(log_entry)

    def load_for_date(self, date: str) -> list[TriageLogEntry]:
        return [e for e in self._entries if e["timestamp"].startswith(date)]


# =============================================================================
# Fake: LLMTriageClient
# =============================================================================


class FakeLLMTriageClient:
    """
    LLMTriageProtocol の固定応答実装

    dict 駆動: entry_id をキーに返す ShardKind を事前指定。
    未登録 entry_id は default を返す。
    呼び出し回数とエントリIDを記録し、テストでアサート可能。
    """

    def __init__(
        self,
        responses: dict[str, ShardKind] | None = None,
        default: ShardKind = "knowledge",
    ) -> None:
        self.responses = responses or {}
        self.default = default
        self.calls: list[str] = []

    def classify(self, entry: RawEntry) -> ShardKind:
        self.calls.append(entry["id"])
        return self.responses.get(entry["id"], self.default)


# =============================================================================
# Fake: EmailParser
# =============================================================================


class FakeEmailParser:
    """
    EmailParserProtocol の固定応答実装

    parse: 注入された単一 EmailMessage を返す
    parse_many: 注入されたリストを返す
    呼び出されたパスを記録。
    """

    def __init__(
        self,
        single: EmailMessage | None = None,
        many: list[EmailMessage] | None = None,
    ) -> None:
        self._single = single
        self._many = many or []
        self.parse_calls: list[Path] = []
        self.parse_many_calls: list[Path] = []

    def parse(self, path: Path) -> EmailMessage:
        self.parse_calls.append(path)
        if self._single is None:
            raise ValueError("FakeEmailParser: single not set")
        return self._single

    def parse_many(self, path: Path) -> list[EmailMessage]:
        self.parse_many_calls.append(path)
        return list(self._many)


# =============================================================================
# Builders
# =============================================================================


def build_email_message(
    *,
    message_id: str = "<default@example.com>",
    from_address: str = "sender@example.com",
    from_name: str = "Sender",
    to_addresses: list[str] | None = None,
    cc_addresses: list[str] | None = None,
    subject: str = "default subject",
    date: datetime | None = None,
    body_text: str = "default body",
    body_html: str | None = None,
    attachments: list[dict[str, Any]] | None = None,
    thread_id: str | None = None,
    in_reply_to: str | None = None,
    references: list[str] | None = None,
) -> EmailMessage:
    """EmailMessage のテストデータを生成（必要分のみオーバーライド）"""
    return {
        "message_id": message_id,
        "from_addr": {"name": from_name, "address": from_address},
        "to_addrs": [
            {"name": "", "address": a}
            for a in (to_addresses or ["recipient@example.com"])
        ],
        "cc_addrs": [{"name": "", "address": a} for a in (cc_addresses or [])],
        "subject": subject,
        "date": date or datetime(2026, 4, 7, 14, 30, 22),
        "body_text": body_text,
        "body_html": body_html,
        "attachments": [
            {
                "filename": a.get("filename", "file.txt"),
                "content_type": a.get("content_type", "text/plain"),
                "size": a.get("size", 0),
            }
            for a in (attachments or [])
        ],
        "thread_id": thread_id,
        "in_reply_to": in_reply_to,
        "references": references or [],
    }


def build_raw_entry(
    *,
    entry_id: str = "email_20260407_143022_abc12345",
    date: str = "2026-04-07",
    time: str = "14:30:22",
    source_type: str = "email",
    from_addr: str = "sender@example.com",
    to_addrs: list[str] | None = None,
    cc_addrs: list[str] | None = None,
    subject: str = "default subject",
    thread_id: str | None = None,
    attachments: list[str] | None = None,
    tags: list[str] | None = None,
    body: str = "default body",
) -> RawEntry:
    """RawEntry のテストデータを生成"""
    return {
        "id": entry_id,
        "date": date,
        "time": time,
        "source_type": source_type,
        "from_addr": from_addr,
        "to_addrs": to_addrs or ["recipient@example.com"],
        "cc_addrs": cc_addrs or [],
        "subject": subject,
        "thread_id": thread_id,
        "attachments": attachments or [],
        "tags": tags or [],
        "body": body,
    }


def build_alias_record(
    *,
    kind: ShardKind = "projects",
    slug: str = "DefaultProject",
    canonical: str = "デフォルト案件",
    aliases: list[str] | None = None,
    target_path: str | None = None,
    archive_status: ArchiveStatus = "active",
) -> AliasRecord:
    """
    AliasRecord のテストデータを生成

    Note:
        target_path 省略時は archive_status に合わせて自動選択:
          - active:    shards/<kind>/<slug>/_project.md (projects 用)
          - completed: archive/<kind>/<slug>/_project.md
          - removed:   shards/<kind>/<slug>/_project.md (元のまま)
    """
    if target_path is None:
        if archive_status == "completed":
            target_path = f"archive/{kind}/{slug}/_project.md"
        else:
            target_path = f"shards/{kind}/{slug}/_project.md"
    return {
        "id": f"{kind}/{slug}",
        "canonical": canonical,
        "aliases": aliases or [],
        "shard": kind,
        "target_path": target_path,
        "archive_status": archive_status,
    }

#!/usr/bin/env python3
"""
thread_id 回帰テスト
=====================

v3 セッションで bootstrap 側の shard_workload.py に
「`*.prod.outlook.com` Message-ID を `outlook.com` alias と誤マッチする」
バグを発見・修正。

production の triage / resolver コードを直接読みで検証した結果:
- rule_engine.py:_extract_field() は subject/body/from/to/cc の 5 フィールドのみ
  → thread_id は検索対象にならない
- alias_resolver_repository.py:_parse() は _ENTRY_RE 完全一致行のみ採用
  → `thread_id:` 行は黙ってスキップされる
- RawEntry.body は frontmatter 除外済みの本文のみ

結論: **production には同種の bug は存在しない**

以下 4 件は、この事実を regression として永続的に検知するテスト。
全件が既存コードで一発 green（修正不要）。
"""

import re

import pytest

from domain.types.triage import TriageMatchField
from infrastructure.repositories.alias_resolver_repository import (
    MarkdownAliasResolverRepository,
)
from test.test_helpers import build_raw_entry

# =============================================================================
# regression tests
# =============================================================================


class TestThreadIdRegression:
    """thread_id が production の triage / resolver を汚染しないことの永続保証"""

    @pytest.mark.unit
    def test_rule_engine_only_scans_designated_fields(self) -> None:
        """_extract_field は subject/body/from/to/cc のみ。thread_id は含まれない。"""
        from application.triage.rule_engine import RuleBasedTriageEngine

        entry = build_raw_entry(
            subject="test",
            body="hello",
            thread_id="FAKE123.prod.outlook.com",
        )
        for field in ("subject", "body", "from", "to", "cc"):
            text = RuleBasedTriageEngine._extract_field(entry, field)  # type: ignore[arg-type]
            assert "FAKE123.prod.outlook.com" not in text

    @pytest.mark.unit
    def test_alias_resolver_repository_ignores_non_entry_lines(self) -> None:
        """_parse は _ENTRY_RE 完全一致行のみ。thread_id 行はスキップされる。"""
        md_with_noise = """\
# Global Index

## vendors/
- [Active](shards/vendors/Active.md) — also: active.com
thread_id: NOISE123.prod.outlook.com
random noise line
"""
        records = MarkdownAliasResolverRepository._parse(md_with_noise)
        assert len(records) == 1
        assert records[0]["id"] == "vendors/Active"

    @pytest.mark.unit
    def test_triage_match_field_does_not_include_thread_id(self) -> None:
        """TriageMatchField Literal は 5 フィールドのみ。thread_id を含まない。"""
        import typing

        args = typing.get_args(TriageMatchField)
        assert "thread_id" not in args
        assert set(args) == {"subject", "body", "from", "to", "cc"}

    @pytest.mark.unit
    def test_raw_entry_body_does_not_contain_thread_id(self) -> None:
        """build_raw_entry の body に thread_id が混入しないことを確認。"""
        entry = build_raw_entry(
            body="本文のみ",
            thread_id="SOMETHING.prod.outlook.com",
        )
        assert "SOMETHING" not in entry["body"]
        assert entry["body"] == "本文のみ"

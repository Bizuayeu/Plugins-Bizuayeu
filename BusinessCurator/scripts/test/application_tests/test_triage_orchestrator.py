#!/usr/bin/env python3
"""
application/triage/triage_orchestrator.py テスト
==================================================

TriageOrchestrator 統合動作検証。

検証ポイント:
- ルール優先 → LLM フォールバック の流れ
- ルールマッチ時は LLM が呼ばれない
- ルール未マッチ時のみ LLM 呼び出し
- 全判定が triage_log に append される
- LLM フォールバックの結果が confidence == "llm_fallback" になる
"""

from datetime import datetime

import pytest

from application.triage.rule_engine import RuleBasedTriageEngine
from application.triage.triage_orchestrator import TriageOrchestrator
from domain.types.triage import TriageRule
from test.test_helpers import (
    FakeClock,
    FakeLLMTriageClient,
    FakeTriageLogRepository,
    build_raw_entry,
)

# =============================================================================
# Helpers
# =============================================================================


def make_subject_rule(
    pattern: str, kind: str = "projects", slug: str = "X"
) -> TriageRule:
    return {
        "pattern": pattern,
        "target_kind": kind,  # type: ignore[typeddict-item]
        "target_slug": slug,
        "match_field": "subject",
    }


def build_orchestrator(
    rules=None,
    llm_responses=None,
    llm_default="knowledge",
    fixed_time=datetime(2026, 4, 7, 14, 30, 22),
):  # type: ignore[no-untyped-def]
    rule_engine = RuleBasedTriageEngine(rules=rules or [])
    llm = FakeLLMTriageClient(responses=llm_responses, default=llm_default)
    log_repo = FakeTriageLogRepository()
    clock = FakeClock(fixed=fixed_time)
    orch = TriageOrchestrator(
        rule_engine=rule_engine, llm_client=llm, log_repository=log_repo, clock=clock
    )
    return orch, llm, log_repo


# =============================================================================
# ルール優先
# =============================================================================


class TestTriageOrchestratorRulePath:
    """ルールマッチ時の動作"""

    @pytest.mark.unit
    def test_rule_match_skips_llm(self) -> None:
        rule = make_subject_rule("○○マンション", kind="projects", slug="MaruMaru")
        orch, llm, log = build_orchestrator(rules=[rule])
        entry = build_raw_entry(subject="○○マンション排煙設備")

        decision = orch.classify(entry)

        assert decision["confidence"] == "rule_match"
        assert decision["primary_shard"] == "projects"
        assert llm.calls == []  # LLM は呼ばれない

    @pytest.mark.unit
    def test_rule_match_appends_to_log(self) -> None:
        rule = make_subject_rule("test")
        orch, _, log = build_orchestrator(rules=[rule])
        entry = build_raw_entry(subject="test subject")
        orch.classify(entry)
        # ログ追記
        assert len(log.load_for_date("2026-04-07")) == 1

    @pytest.mark.unit
    def test_log_entry_has_llm_invoked_false_on_rule_match(self) -> None:
        rule = make_subject_rule("test")
        orch, _, log = build_orchestrator(rules=[rule])
        entry = build_raw_entry(subject="test")
        orch.classify(entry)
        log_entry = log.load_for_date("2026-04-07")[0]
        assert log_entry["llm_invoked"] is False


# =============================================================================
# LLM フォールバック
# =============================================================================


class TestTriageOrchestratorLLMFallback:
    """ルール未マッチ時の LLM 呼び出し"""

    @pytest.mark.unit
    def test_no_match_invokes_llm(self) -> None:
        orch, llm, _ = build_orchestrator(rules=[])
        entry = build_raw_entry(entry_id="email_20260407_143022_aaaaaaaa", subject="X")
        orch.classify(entry)
        assert llm.calls == ["email_20260407_143022_aaaaaaaa"]

    @pytest.mark.unit
    def test_llm_response_becomes_primary_shard(self) -> None:
        orch, _, _ = build_orchestrator(
            rules=[],
            llm_responses={"email_20260407_143022_aaaaaaaa": "vendors"},
        )
        entry = build_raw_entry(entry_id="email_20260407_143022_aaaaaaaa")
        decision = orch.classify(entry)
        assert decision["primary_shard"] == "vendors"
        assert decision["confidence"] == "llm_fallback"

    @pytest.mark.unit
    def test_llm_default_used_when_no_specific_response(self) -> None:
        orch, _, _ = build_orchestrator(rules=[], llm_default="knowledge")
        entry = build_raw_entry()
        decision = orch.classify(entry)
        assert decision["primary_shard"] == "knowledge"

    @pytest.mark.unit
    def test_llm_log_marked_invoked(self) -> None:
        orch, _, log = build_orchestrator(rules=[])
        entry = build_raw_entry()
        orch.classify(entry)
        log_entry = log.load_for_date("2026-04-07")[0]
        assert log_entry["llm_invoked"] is True

    @pytest.mark.unit
    def test_llm_call_count_per_classify(self) -> None:
        """ルール未マッチ時 LLM 呼び出しは1回のみ"""
        orch, llm, _ = build_orchestrator(rules=[])
        entry = build_raw_entry()
        orch.classify(entry)
        assert len(llm.calls) == 1


# =============================================================================
# バッチ
# =============================================================================


class TestTriageOrchestratorBatch:
    """classify_many"""

    @pytest.mark.unit
    def test_classify_many_returns_decisions_in_order(self) -> None:
        rule = make_subject_rule("M", kind="projects", slug="P")
        orch, _, _ = build_orchestrator(rules=[rule])
        entries = [
            build_raw_entry(entry_id="email_20260407_143022_aaaaaaaa", subject="M"),
            build_raw_entry(entry_id="email_20260407_143022_bbbbbbbb", subject="N"),
            build_raw_entry(entry_id="email_20260407_143022_cccccccc", subject="M"),
        ]
        decisions = orch.classify_many(entries)
        assert [d["entry_id"] for d in decisions] == [
            "email_20260407_143022_aaaaaaaa",
            "email_20260407_143022_bbbbbbbb",
            "email_20260407_143022_cccccccc",
        ]

    @pytest.mark.unit
    def test_classify_many_logs_each(self) -> None:
        orch, _, log = build_orchestrator(rules=[])
        entries = [
            build_raw_entry(entry_id="email_20260407_143022_aaaaaaaa"),
            build_raw_entry(entry_id="email_20260407_143022_bbbbbbbb"),
        ]
        orch.classify_many(entries)
        assert len(log.load_for_date("2026-04-07")) == 2

    @pytest.mark.unit
    def test_classify_many_mixed_rule_and_llm(self) -> None:
        rule = make_subject_rule("matched", kind="projects", slug="P")
        orch, llm, _ = build_orchestrator(
            rules=[rule],
            llm_responses={"email_20260407_143022_bbbbbbbb": "clients"},
        )
        entries = [
            build_raw_entry(
                entry_id="email_20260407_143022_aaaaaaaa", subject="matched"
            ),
            build_raw_entry(
                entry_id="email_20260407_143022_bbbbbbbb", subject="not in rules"
            ),
        ]
        decisions = orch.classify_many(entries)
        # LLM は1件しか呼ばれない（ルールマッチをスキップ）
        assert llm.calls == ["email_20260407_143022_bbbbbbbb"]
        assert decisions[0]["confidence"] == "rule_match"
        assert decisions[1]["confidence"] == "llm_fallback"


# =============================================================================
# Clock の利用
# =============================================================================


class TestTriageOrchestratorClock:
    """timestamp の決定的注入"""

    @pytest.mark.unit
    def test_log_timestamp_uses_clock(self) -> None:
        orch, _, log = build_orchestrator(
            rules=[], fixed_time=datetime(2026, 5, 1, 12, 0, 0)
        )
        entry = build_raw_entry()
        orch.classify(entry)
        log_entry = log.load_for_date("2026-05-01")[0]
        assert log_entry["timestamp"].startswith("2026-05-01T12:00:00")

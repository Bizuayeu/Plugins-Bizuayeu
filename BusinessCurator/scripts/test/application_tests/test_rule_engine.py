#!/usr/bin/env python3
"""
application/triage/rule_engine.py テスト
=========================================

RuleBasedTriageEngine の判定動作検証。

不変条件 (property-based):
1. decisionは必ず生成される（Noneを返さない）
2. 主シャードは最大1つ
3. ルールマッチ1件以上ならconfidence == "rule_match"

業務計画書 §7.3 「ルールで8割、LLM で2割」設計仮説の Python 部分。
"""

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from application.triage.rule_engine import RuleBasedTriageEngine
from domain.types.triage import TriageRule
from test.test_helpers import build_raw_entry

# =============================================================================
# Helpers
# =============================================================================


def make_subject_rule(
    pattern: str, target_kind: str = "projects", target_slug: str = "X"
) -> TriageRule:
    return {
        "pattern": pattern,
        "target_kind": target_kind,  # type: ignore[typeddict-item]
        "target_slug": target_slug,
        "match_field": "subject",
    }


def make_from_rule(
    pattern: str, target_kind: str = "clients", target_slug: str = "Y"
) -> TriageRule:
    return {
        "pattern": pattern,
        "target_kind": target_kind,  # type: ignore[typeddict-item]
        "target_slug": target_slug,
        "match_field": "from",
    }


def make_body_rule(
    pattern: str, target_kind: str = "knowledge", target_slug: str = "Z"
) -> TriageRule:
    return {
        "pattern": pattern,
        "target_kind": target_kind,  # type: ignore[typeddict-item]
        "target_slug": target_slug,
        "match_field": "body",
    }


# =============================================================================
# 基本動作
# =============================================================================


class TestRuleBasedTriageEngineBasic:
    @pytest.mark.unit
    def test_no_rules_no_match(self) -> None:
        engine = RuleBasedTriageEngine(rules=[])
        entry = build_raw_entry()
        decision = engine.classify(entry)
        assert decision["confidence"] == "unclassified"
        assert decision["primary_shard"] is None
        assert decision["matched_rules"] == []

    @pytest.mark.unit
    def test_subject_match_creates_rule_match(self) -> None:
        rule = make_subject_rule(
            r"○○マンション", target_kind="projects", target_slug="MaruMaru"
        )
        engine = RuleBasedTriageEngine(rules=[rule])
        entry = build_raw_entry(subject="○○マンション排煙設備")
        decision = engine.classify(entry)
        assert decision["confidence"] == "rule_match"
        assert decision["primary_shard"] == "projects"
        assert decision["primary_slug"] == "MaruMaru"

    @pytest.mark.unit
    def test_from_match(self) -> None:
        rule = make_from_rule(
            r"@meguru\.example\.jp", target_kind="clients", target_slug="Meguru"
        )
        engine = RuleBasedTriageEngine(rules=[rule])
        entry = build_raw_entry(from_addr="yamada@meguru.example.jp")
        decision = engine.classify(entry)
        assert decision["confidence"] == "rule_match"
        assert decision["primary_shard"] == "clients"

    @pytest.mark.unit
    def test_body_match(self) -> None:
        rule = make_body_rule(r"排煙告示", target_kind="knowledge", target_slug="houki")
        engine = RuleBasedTriageEngine(rules=[rule])
        entry = build_raw_entry(body="排煙告示の解釈について")
        decision = engine.classify(entry)
        assert decision["confidence"] == "rule_match"
        assert decision["primary_shard"] == "knowledge"

    @pytest.mark.unit
    def test_no_match_returns_unclassified(self) -> None:
        rule = make_subject_rule(r"foobar")
        engine = RuleBasedTriageEngine(rules=[rule])
        entry = build_raw_entry(subject="まったく違う件名")
        decision = engine.classify(entry)
        assert decision["confidence"] == "unclassified"


# =============================================================================
# 複数ルール / 主シャード優先順位
# =============================================================================


class TestRuleBasedTriageEnginePriority:
    @pytest.mark.unit
    def test_first_match_becomes_primary(self) -> None:
        """最初にマッチしたルールが primary_shard"""
        r1 = make_subject_rule(
            r"○○マンション", target_kind="projects", target_slug="P1"
        )
        r2 = make_from_rule(r"@meguru", target_kind="clients", target_slug="C1")
        engine = RuleBasedTriageEngine(rules=[r1, r2])
        entry = build_raw_entry(
            subject="○○マンション", from_addr="yamada@meguru.example.jp"
        )
        decision = engine.classify(entry)
        assert decision["primary_shard"] == "projects"
        assert decision["primary_slug"] == "P1"

    @pytest.mark.unit
    def test_secondary_matches_become_tags(self) -> None:
        r1 = make_subject_rule(
            r"○○マンション", target_kind="projects", target_slug="P1"
        )
        r2 = make_from_rule(r"@meguru", target_kind="clients", target_slug="C1")
        engine = RuleBasedTriageEngine(rules=[r1, r2])
        entry = build_raw_entry(subject="○○マンション", from_addr="x@meguru.example.jp")
        decision = engine.classify(entry)
        assert "clients/C1" in decision["secondary_tags"]

    @pytest.mark.unit
    def test_matched_rules_listed(self) -> None:
        r1 = make_subject_rule(r"X")
        engine = RuleBasedTriageEngine(rules=[r1])
        entry = build_raw_entry(subject="X")
        decision = engine.classify(entry)
        assert "X" in decision["matched_rules"]

    @pytest.mark.unit
    def test_invalid_regex_in_rule_raises(self) -> None:
        bad_rule = make_subject_rule(r"[invalid")
        from domain.exceptions import TriageError

        with pytest.raises(TriageError):
            RuleBasedTriageEngine(rules=[bad_rule])

    @pytest.mark.unit
    def test_to_field_match(self) -> None:
        """match_field='to' のマッチ"""
        rule: TriageRule = {
            "pattern": r"@meguru",
            "target_kind": "clients",
            "target_slug": "Meg",
            "match_field": "to",
        }
        engine = RuleBasedTriageEngine(rules=[rule])
        entry = build_raw_entry(to_addrs=["a@meguru.example.jp", "b@other.com"])
        decision = engine.classify(entry)
        assert decision["confidence"] == "rule_match"

    @pytest.mark.unit
    def test_cc_field_match(self) -> None:
        """match_field='cc' のマッチ"""
        rule: TriageRule = {
            "pattern": r"@vendor",
            "target_kind": "vendors",
            "target_slug": "V",
            "match_field": "cc",
        }
        engine = RuleBasedTriageEngine(rules=[rule])
        entry = build_raw_entry(cc_addrs=["x@vendor.jp"])
        decision = engine.classify(entry)
        assert decision["confidence"] == "rule_match"


# =============================================================================
# Property-based: 不変条件3つ
# =============================================================================


_text_strategy = st.text(min_size=0, max_size=50)


@st.composite
def _entry_strategy(draw):  # type: ignore[no-untyped-def]
    return build_raw_entry(
        entry_id=f"email_20260407_143022_{draw(st.text(alphabet='0123456789abcdef', min_size=8, max_size=8))}",
        subject=draw(_text_strategy),
        body=draw(_text_strategy),
        from_addr=draw(st.text(min_size=1, max_size=30)),
    )


_word_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll")),
    min_size=1,
    max_size=10,
)


@st.composite
def _rule_strategy(draw):  # type: ignore[no-untyped-def]
    field = draw(st.sampled_from(["subject", "body", "from"]))
    pattern = draw(_word_strategy)
    kind = draw(st.sampled_from(["projects", "clients", "vendors", "knowledge"]))
    slug = draw(_word_strategy)
    return {
        "pattern": pattern,
        "target_kind": kind,
        "target_slug": slug,
        "match_field": field,
    }


class TestRuleBasedTriageEngineProperties:
    """不変条件 (業務計画書 §4.2)"""

    @pytest.mark.property
    @given(entry=_entry_strategy(), rules=st.lists(_rule_strategy(), max_size=5))
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_invariant_decision_always_generated(self, entry, rules) -> None:  # type: ignore[no-untyped-def]
        """不変条件1: decision は必ず生成される"""
        engine = RuleBasedTriageEngine(rules=rules)
        decision = engine.classify(entry)
        assert decision is not None
        assert "entry_id" in decision

    @pytest.mark.property
    @given(entry=_entry_strategy(), rules=st.lists(_rule_strategy(), max_size=5))
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_invariant_at_most_one_primary(self, entry, rules) -> None:  # type: ignore[no-untyped-def]
        """不変条件2: 主シャードは最大1つ"""
        engine = RuleBasedTriageEngine(rules=rules)
        decision = engine.classify(entry)
        # primary_shard は単一の Optional[ShardKind]
        assert decision["primary_shard"] is None or isinstance(
            decision["primary_shard"], str
        )
        # primary_slug は primary_shard が None の場合 None
        if decision["primary_shard"] is None:
            assert decision["primary_slug"] is None

    @pytest.mark.property
    @given(
        entry=_entry_strategy(),
        rules=st.lists(_rule_strategy(), min_size=1, max_size=5),
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_invariant_match_implies_rule_match_confidence(self, entry, rules) -> None:  # type: ignore[no-untyped-def]
        """不変条件3: matched_rules が1件以上 → confidence == 'rule_match'"""
        engine = RuleBasedTriageEngine(rules=rules)
        decision = engine.classify(entry)
        if decision["matched_rules"]:
            assert decision["confidence"] == "rule_match"
        else:
            assert decision["confidence"] == "unclassified"

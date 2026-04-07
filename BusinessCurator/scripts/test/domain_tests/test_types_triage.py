#!/usr/bin/env python3
"""
domain/types/triage.py テスト
=============================

TriageRule / TriageDecision / TriageLogEntry のフィールド検証。

設計意図:
- TriageRule: ルールベース triage の判定パターン（正規表現）
- TriageDecision: 1エントリへの判定結果（主シャード+副タグ複数）
- TriageLogEntry: triage_logs/_triage_log_YYYYMMDD.json の1行
- LLMフォールバック呼び出しの有無も TriageDecision に記録
"""

from typing import List, Literal, Optional, get_type_hints

import pytest

from domain.types.triage import (
    TriageConfidence,
    TriageDecision,
    TriageLogEntry,
    TriageRule,
)

# =============================================================================
# TriageConfidence
# =============================================================================


class TestTriageConfidence:
    """TriageConfidence Literal のテスト"""

    @pytest.mark.unit
    def test_rule_match_is_valid(self) -> None:
        """rule_match: ルールベース確定"""
        c: TriageConfidence = "rule_match"
        assert c == "rule_match"

    @pytest.mark.unit
    def test_llm_fallback_is_valid(self) -> None:
        """llm_fallback: LLM 判定"""
        c: TriageConfidence = "llm_fallback"
        assert c == "llm_fallback"

    @pytest.mark.unit
    def test_unclassified_is_valid(self) -> None:
        """unclassified: 分類不能（保留）"""
        c: TriageConfidence = "unclassified"
        assert c == "unclassified"


# =============================================================================
# TriageRule
# =============================================================================


class TestTriageRule:
    """TriageRule TypedDict のテスト"""

    @pytest.mark.unit
    def test_has_pattern_field(self) -> None:
        """pattern フィールド（正規表現文字列）"""
        hints = get_type_hints(TriageRule)
        assert "pattern" in hints
        assert hints["pattern"] is str

    @pytest.mark.unit
    def test_has_target_kind_field(self) -> None:
        """target_kind フィールド（ShardKind）"""
        hints = get_type_hints(TriageRule)
        assert "target_kind" in hints

    @pytest.mark.unit
    def test_has_target_slug_field(self) -> None:
        """target_slug フィールド（マッチ時の振り先 slug）"""
        hints = get_type_hints(TriageRule)
        assert "target_slug" in hints
        assert hints["target_slug"] is str

    @pytest.mark.unit
    def test_has_match_field_field(self) -> None:
        """match_field フィールド（subject/body/from/to などマッチ対象）"""
        hints = get_type_hints(TriageRule)
        assert "match_field" in hints

    @pytest.mark.unit
    def test_can_construct(self) -> None:
        """物件識別子マッチルールの構築"""
        rule: TriageRule = {
            "pattern": r"○○マンション|○○MS|2026-003",
            "target_kind": "projects",
            "target_slug": "MaruMaruMansion",
            "match_field": "subject",
        }
        assert rule["target_kind"] == "projects"


# =============================================================================
# TriageDecision
# =============================================================================


class TestTriageDecision:
    """TriageDecision TypedDict のテスト"""

    @pytest.mark.unit
    def test_has_entry_id_field(self) -> None:
        """entry_id フィールド（対象エントリID）"""
        hints = get_type_hints(TriageDecision)
        assert "entry_id" in hints
        assert hints["entry_id"] is str

    @pytest.mark.unit
    def test_has_primary_shard_field(self) -> None:
        """primary_shard フィールド（主シャード、None=保留）"""
        hints = get_type_hints(TriageDecision)
        assert "primary_shard" in hints

    @pytest.mark.unit
    def test_has_primary_slug_field(self) -> None:
        """primary_slug フィールド（主シャード内の slug、None 許容）"""
        hints = get_type_hints(TriageDecision)
        assert "primary_slug" in hints
        assert hints["primary_slug"] == Optional[str]

    @pytest.mark.unit
    def test_has_secondary_tags_field(self) -> None:
        """secondary_tags フィールド（副タグ、複数）"""
        hints = get_type_hints(TriageDecision)
        assert "secondary_tags" in hints
        assert hints["secondary_tags"] == List[str]

    @pytest.mark.unit
    def test_has_confidence_field(self) -> None:
        """confidence フィールド（rule_match / llm_fallback / unclassified）"""
        hints = get_type_hints(TriageDecision)
        assert "confidence" in hints

    @pytest.mark.unit
    def test_has_matched_rules_field(self) -> None:
        """matched_rules フィールド（適用されたルール pattern のリスト）"""
        hints = get_type_hints(TriageDecision)
        assert "matched_rules" in hints
        assert hints["matched_rules"] == List[str]

    @pytest.mark.unit
    def test_can_construct_rule_match(self) -> None:
        """ルールマッチによる判定の構築"""
        decision: TriageDecision = {
            "entry_id": "email_20260407_143022_abc123",
            "primary_shard": "projects",
            "primary_slug": "MaruMaruMansion",
            "secondary_tags": ["clients/ShikakuFudosan"],
            "confidence": "rule_match",
            "matched_rules": [r"○○マンション|○○MS"],
        }
        assert decision["confidence"] == "rule_match"
        assert decision["primary_shard"] == "projects"

    @pytest.mark.unit
    def test_can_construct_unclassified(self) -> None:
        """分類不能エントリの構築（primary_shard=None）"""
        decision: TriageDecision = {
            "entry_id": "email_20260407_100000_def456",
            "primary_shard": None,
            "primary_slug": None,
            "secondary_tags": [],
            "confidence": "unclassified",
            "matched_rules": [],
        }
        assert decision["primary_shard"] is None
        assert decision["confidence"] == "unclassified"


# =============================================================================
# TriageLogEntry
# =============================================================================


class TestTriageLogEntry:
    """TriageLogEntry TypedDict のテスト"""

    @pytest.mark.unit
    def test_has_timestamp_field(self) -> None:
        """timestamp フィールド（ISO 8601 文字列）"""
        hints = get_type_hints(TriageLogEntry)
        assert "timestamp" in hints
        assert hints["timestamp"] is str

    @pytest.mark.unit
    def test_has_decision_field(self) -> None:
        """decision フィールド（TriageDecision を含む）"""
        hints = get_type_hints(TriageLogEntry)
        assert "decision" in hints

    @pytest.mark.unit
    def test_has_llm_invoked_field(self) -> None:
        """llm_invoked フィールド（LLM フォールバックが呼ばれたか）"""
        hints = get_type_hints(TriageLogEntry)
        assert "llm_invoked" in hints
        assert hints["llm_invoked"] is bool

    @pytest.mark.unit
    def test_can_construct(self) -> None:
        """ログエントリ構築"""
        decision: TriageDecision = {
            "entry_id": "email_20260407_143022_abc123",
            "primary_shard": "projects",
            "primary_slug": "MaruMaruMansion",
            "secondary_tags": [],
            "confidence": "rule_match",
            "matched_rules": [r"○○マンション"],
        }
        log: TriageLogEntry = {
            "timestamp": "2026-04-07T14:35:00+09:00",
            "decision": decision,
            "llm_invoked": False,
        }
        assert log["llm_invoked"] is False
        assert log["decision"]["entry_id"] == "email_20260407_143022_abc123"

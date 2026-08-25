#!/usr/bin/env python3
"""
Triage Domain Types
===================

ルールベース triage と LLM フォールバックの判定を表現する型群。

設計意図:
- TriageRule: manager 層が登録するエンティティから機械生成される正規表現ルール
- TriageDecision: 1エントリへの判定結果。主シャード最大1つ + 副タグ複数
- TriageLogEntry: 日次 JSON ログの1行。LLM 呼び出しの有無も記録
- 業務計画書 §7.3 「ルールで8割、LLM で2割」設計仮説の検証用
"""

from typing import Literal, TypedDict

from domain.types.shard import ShardKind

# =============================================================================
# Confidence
# =============================================================================

TriageConfidence = Literal["rule_match", "llm_fallback", "unclassified"]
"""判定信頼度。

- rule_match: ルールベースで確定（最も確信度が高い）
- llm_fallback: LLM 判定（中程度）
- unclassified: 判定不能（inbox/unclassified/ に保留）
"""


# =============================================================================
# TriageRule
# =============================================================================

TriageMatchField = Literal["subject", "body", "from", "to", "cc"]
"""ルールマッチ対象フィールド。"""


class TriageRule(TypedDict):
    """
    ルールベース triage の判定パターン

    Attributes:
        pattern: 正規表現文字列（コンパイル前）
        target_kind: マッチ時の振り先シャード種別
        target_slug: マッチ時の振り先 slug
        match_field: マッチ対象フィールド
    """

    pattern: str
    target_kind: ShardKind
    target_slug: str
    match_field: TriageMatchField


# =============================================================================
# TriageDecision
# =============================================================================


class TriageDecision(TypedDict):
    """
    1エントリへの triage 判定結果

    Attributes:
        entry_id: 判定対象のエントリ ID
        primary_shard: 主シャード（unclassified 時は None）
        primary_slug: 主シャード内 slug（None 許容）
        secondary_tags: 副タグ（"clients/ShikakuFudosan" 形式の文字列）
        confidence: 判定信頼度
        matched_rules: 適用された TriageRule.pattern のリスト
    """

    entry_id: str
    primary_shard: ShardKind | None
    primary_slug: str | None
    secondary_tags: list[str]
    confidence: TriageConfidence
    matched_rules: list[str]


# =============================================================================
# TriageLogEntry
# =============================================================================


class TriageLogEntry(TypedDict):
    """
    triage_logs/_triage_log_YYYYMMDD.json の1行

    Attributes:
        timestamp: 判定実行時刻（ISO 8601 文字列）
        decision: 判定結果
        llm_invoked: LLM フォールバックが呼ばれたかどうか
    """

    timestamp: str
    decision: TriageDecision
    llm_invoked: bool


__all__ = [
    "TriageConfidence",
    "TriageDecision",
    "TriageLogEntry",
    "TriageMatchField",
    "TriageRule",
]

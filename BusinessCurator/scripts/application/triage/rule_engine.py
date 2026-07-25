#!/usr/bin/env python3
"""
RuleBasedTriageEngine
=====================

ルールベース triage 判定エンジン。

設計意図:
- 業務計画書 §7.3 「ルールで8割」設計仮説の Python 部分
- 残り2割は TriageOrchestrator 経由で LLM フォールバック
- ルール: subject/body/from/to/cc を正規表現マッチ
- 主シャード: 最初にマッチしたルールの target_kind/slug
- 副タグ: それ以外のマッチを "kind/slug" 文字列として保持

不変条件:
1. classify は必ず TriageDecision を返す（None なし）
2. primary_shard は単一（最初のマッチのみ）
3. matched_rules が1件以上なら confidence == "rule_match"
"""

import re
from typing import List, Sequence

from domain.exceptions import TriageError
from domain.types.entry import RawEntry
from domain.types.triage import TriageDecision, TriageMatchField, TriageRule

__all__ = ["RuleBasedTriageEngine"]


class RuleBasedTriageEngine:
    """正規表現ベースの triage エンジン"""

    def __init__(self, rules: Sequence[TriageRule]) -> None:
        """
        Args:
            rules: 判定ルール（順序重要：先頭から評価され最初のマッチが primary）

        Raises:
            TriageError: ルールの正規表現がコンパイル失敗
        """
        self._rules: List[TriageRule] = list(rules)
        self._compiled: List[re.Pattern[str]] = []
        for rule in self._rules:
            try:
                self._compiled.append(re.compile(rule["pattern"]))
            except re.error as e:
                raise TriageError(f"invalid regex in rule: {rule['pattern']!r} ({e})") from e

    def classify(self, entry: RawEntry) -> TriageDecision:
        """
        エントリに対し全ルールを評価し TriageDecision を返す

        Args:
            entry: 判定対象

        Returns:
            TriageDecision（unclassified もしくは rule_match）
        """
        primary_shard = None
        primary_slug = None
        secondary_tags: List[str] = []
        matched_patterns: List[str] = []

        for rule, pattern in zip(self._rules, self._compiled):
            target_text = self._extract_field(entry, rule["match_field"])
            if pattern.search(target_text):
                matched_patterns.append(rule["pattern"])
                if primary_shard is None:
                    primary_shard = rule["target_kind"]
                    primary_slug = rule["target_slug"]
                else:
                    tag = f"{rule['target_kind']}/{rule['target_slug']}"
                    if tag not in secondary_tags:
                        secondary_tags.append(tag)

        confidence: str
        if matched_patterns:
            confidence = "rule_match"
        else:
            confidence = "unclassified"

        return {
            "entry_id": entry["id"],
            "primary_shard": primary_shard,
            "primary_slug": primary_slug,
            "secondary_tags": secondary_tags,
            "confidence": confidence,  # type: ignore[typeddict-item]
            "matched_rules": matched_patterns,
        }

    @staticmethod
    def _extract_field(entry: RawEntry, field: TriageMatchField) -> str:
        """match_field に応じた検索対象テキストを返す"""
        if field == "subject":
            return entry["subject"]
        if field == "body":
            return entry["body"]
        if field == "from":
            return entry["from_addr"]
        if field == "to":
            return " ".join(entry["to_addrs"])
        # field == "cc" (Literal 型でガード済み、他値は不可)
        return " ".join(entry["cc_addrs"])

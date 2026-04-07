#!/usr/bin/env python3
"""
TriageOrchestrator
==================

ルールベース → LLM フォールバックの triage オーケストレーター。

設計意図:
- RuleBasedTriageEngine を先に試行（業務計画書 §7.3 「8割」）
- ルール未マッチのみ LLMTriageProtocol.classify を呼ぶ
- 全判定を TriageLogRepositoryProtocol に追記
- ClockProtocol で timestamp を決定的に注入（テスト容易）
"""

from typing import List, Sequence

from application.triage.rule_engine import RuleBasedTriageEngine
from domain.protocols import (
    ClockProtocol,
    LLMTriageProtocol,
    TriageLogRepositoryProtocol,
)
from domain.types.entry import RawEntry
from domain.types.triage import TriageDecision, TriageLogEntry

__all__ = ["TriageOrchestrator"]


class TriageOrchestrator:
    """rule_match → llm_fallback の二段階 triage"""

    def __init__(
        self,
        rule_engine: RuleBasedTriageEngine,
        llm_client: LLMTriageProtocol,
        log_repository: TriageLogRepositoryProtocol,
        clock: ClockProtocol,
    ) -> None:
        self._rule_engine = rule_engine
        self._llm = llm_client
        self._log_repo = log_repository
        self._clock = clock

    def classify(self, entry: RawEntry) -> TriageDecision:
        """
        単一エントリを判定し、ログに追記して返す

        Args:
            entry: 判定対象

        Returns:
            TriageDecision（confidence は rule_match か llm_fallback）
        """
        decision = self._rule_engine.classify(entry)
        llm_invoked = False

        if decision["confidence"] == "unclassified":
            shard = self._llm.classify(entry)
            decision = {
                "entry_id": entry["id"],
                "primary_shard": shard,
                "primary_slug": None,
                "secondary_tags": [],
                "confidence": "llm_fallback",
                "matched_rules": [],
            }
            llm_invoked = True

        self._append_log(decision, llm_invoked)
        return decision

    def classify_many(self, entries: Sequence[RawEntry]) -> List[TriageDecision]:
        """
        複数エントリを順番に判定

        Args:
            entries: 判定対象エントリ列

        Returns:
            TriageDecision のリスト（入力順）
        """
        return [self.classify(e) for e in entries]

    def _append_log(self, decision: TriageDecision, llm_invoked: bool) -> None:
        log_entry: TriageLogEntry = {
            "timestamp": self._clock.now().isoformat(),
            "decision": decision,
            "llm_invoked": llm_invoked,
        }
        self._log_repo.append(log_entry)

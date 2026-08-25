#!/usr/bin/env python3
"""
triage_cli
==========

raw-entries/ 全件を triage して triage_logs/ に追記する CLI。

ルール生成:
- alias resolver のアクティブレコードから自動生成
- canonical / aliases を subject 検索パターンに変換
- target_kind = レコードの shard, target_slug = レコードの slug

LLM フォールバック:
- デフォルト: ClaudeCliTriageClient（subprocess `claude -p`）
- --no-llm: フォールバック無効化（unclassified のまま）

JSON 出力スキーマ:
    {
        "status": "ok",
        "total": <int>,
        "rule_match": <int>,
        "llm_fallback": <int>,
        "unclassified": <int>
    }

Composition Root:
    PathResolver
      → MarkdownAliasResolverRepository → ResolverService → rules
      → FileEntryRepository → entries
      → JsonTriageLogRepository → log
      → ClaudeCliTriageClient (or _NullLLMClient)
      → SystemClock
      → RuleBasedTriageEngine + TriageOrchestrator
"""

import argparse
import re
import sys
from pathlib import Path

from application.triage.rule_engine import RuleBasedTriageEngine
from application.triage.triage_orchestrator import TriageOrchestrator
from domain.exceptions import BusinessCuratorError
from domain.types.alias import AliasRecord
from domain.types.entry import RawEntry
from domain.types.triage import TriageLogEntry, TriageRule
from infrastructure.clock import SystemClock
from infrastructure.llm.claude_cli_client import ClaudeCliTriageClient
from infrastructure.path_resolver import PathResolver
from infrastructure.repositories.alias_resolver_repository import (
    MarkdownAliasResolverRepository,
)
from infrastructure.repositories.entry_repository import FileEntryRepository
from infrastructure.repositories.triage_log_repository import JsonTriageLogRepository
from interfaces.cli_helpers import output_error, output_json

__all__ = ["main"]


# =============================================================================
# Rule generation
# =============================================================================


def _build_rules_from_resolver(records: list[AliasRecord]) -> list[TriageRule]:
    """
    アクティブな AliasRecord 群からルール群を生成

    Args:
        records: alias resolver から取得したレコード（archived 含む可）

    Returns:
        TriageRule のリスト

    Note:
        - canonical を subject パターンに（regex エスケープ）
        - aliases も同様
        - target_kind/slug は record の shard/slug
        - 非 active (completed/removed) レコードは除外
    """
    rules: list[TriageRule] = []
    for rec in records:
        if rec["archive_status"] != "active":
            continue
        # ID から slug を抽出
        _, _, slug = rec["id"].partition("/")
        names = [rec["canonical"], *rec["aliases"]]
        for name in names:
            if not name.strip():
                continue
            rules.append(
                {
                    "pattern": re.escape(name),
                    "target_kind": rec["shard"],
                    "target_slug": slug,
                    "match_field": "subject",
                }
            )
    return rules


# =============================================================================
# argparse
# =============================================================================


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m interfaces.triage_cli",
        description="Triage all raw entries against alias resolver rules",
    )
    parser.add_argument("--plugin-root", required=True)
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Disable LLM fallback (unclassified entries stay unclassified)",
    )
    return parser


# =============================================================================
# main
# =============================================================================


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    plugin_root = Path(args.plugin_root)
    resolver = PathResolver(plugin_root)

    # entries
    entries: list[RawEntry] = []
    if resolver.raw_entries_dir.exists():
        entry_repo = FileEntryRepository(raw_entries_dir=resolver.raw_entries_dir)
        entries = entry_repo.list_all()

    # rules from resolver
    alias_repo = MarkdownAliasResolverRepository(file_path=resolver.alias_resolver_path)
    alias_records = alias_repo.load_all()
    rules = _build_rules_from_resolver(alias_records)

    # triage components
    try:
        rule_engine = RuleBasedTriageEngine(rules=rules)
    except BusinessCuratorError as e:
        output_error(f"failed to compile rules: {e}")

    log_repo = JsonTriageLogRepository(triage_logs_dir=resolver.triage_logs_dir)
    clock = SystemClock()

    rule_match = 0
    llm_fallback = 0
    unclassified = 0

    if args.no_llm:
        # rule_engine 直接呼び出し（LLM フォールバックを完全スキップ）
        for entry in entries:
            decision = rule_engine.classify(entry)
            log_entry: TriageLogEntry = {
                "timestamp": clock.now().isoformat(),
                "decision": decision,
                "llm_invoked": False,
            }
            log_repo.append(log_entry)
            if decision["confidence"] == "rule_match":
                rule_match += 1
            else:
                unclassified += 1
    else:
        llm_client = ClaudeCliTriageClient()
        orch = TriageOrchestrator(
            rule_engine=rule_engine,
            llm_client=llm_client,
            log_repository=log_repo,
            clock=clock,
        )
        try:
            decisions = orch.classify_many(entries)
        except BusinessCuratorError as e:
            output_error(f"triage failed: {e}")
        for d in decisions:
            if d["confidence"] == "rule_match":
                rule_match += 1
            elif d["confidence"] == "llm_fallback":
                llm_fallback += 1
            else:
                unclassified += 1

    output_json(
        {
            "status": "ok",
            "total": len(entries),
            "rule_match": rule_match,
            "llm_fallback": llm_fallback,
            "unclassified": unclassified,
        }
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
ClaudeCliTriageClient
=====================

LLMTriageProtocol の `claude -p` subprocess 実装。

設計意図:
- メモリ「APIキーよりサブスク前提」: Anthropic API 直叩き禁止
- subprocess.run(["claude", "-p", prompt, "--output-format", "json", "--json-schema", ...]) で外部 CLI を呼び出し
- 書式は JSON Schema（category を ShardKind の enum に固定）が強制し、応答封筒の structured_output を読む
- 不正レスポンス・タイムアウト・CLI 不在を TriageError に変換
- テストでは subprocess.run を unittest.mock.patch でスタブ化（CI 互換）
"""

import json
import subprocess

from domain.exceptions import TriageError
from domain.types.entry import RawEntry
from domain.types.shard import SHARD_KINDS, ShardKind

__all__ = ["ClaudeCliTriageClient"]


_DEFAULT_TIMEOUT_SECONDS = 60


_PROMPT_TEMPLATE = """\
Classify the following business email into one of these categories:
- projects: project-related emails (specific construction sites, deliverables)
- clients: client-related communications (customers, sales)
- vendors: vendor/supplier communications (purchases, subcontractors)
- knowledge: general knowledge, regulations, standards

Subject: {subject}
From: {from_addr}
Body:
{body}
"""

# 書式はスキーマが強制する（claude -p --json-schema）。散文で「1 語だけ返せ」と縛らない
_OUTPUT_SCHEMA = json.dumps(
    {
        "type": "object",
        "properties": {"category": {"type": "string", "enum": sorted(SHARD_KINDS)}},
        "required": ["category"],
        "additionalProperties": False,
    }
)


class ClaudeCliTriageClient:
    """`claude -p` を呼び出す LLMTriageProtocol 実装"""

    def __init__(self, timeout_seconds: int = _DEFAULT_TIMEOUT_SECONDS) -> None:
        self._timeout = timeout_seconds

    def classify(self, entry: RawEntry) -> ShardKind:
        """
        エントリを LLM で分類

        Args:
            entry: 判定対象

        Returns:
            ShardKind

        Raises:
            TriageError: subprocess 失敗 / 空応答 / 不正シャード / タイムアウト / CLI 不在
        """
        prompt = _PROMPT_TEMPLATE.format(
            subject=entry["subject"],
            from_addr=entry["from_addr"],
            body=entry["body"][:1000],  # body は先頭 1000 文字に切り詰め
        )

        try:
            result = subprocess.run(
                [
                    "claude",
                    "-p",
                    prompt,
                    "--output-format",
                    "json",
                    "--json-schema",
                    _OUTPUT_SCHEMA,
                ],
                capture_output=True,
                text=True,
                timeout=self._timeout,
            )
        except subprocess.TimeoutExpired as e:
            raise TriageError(
                f"claude CLI timeout after {self._timeout}s for entry {entry['id']}"
            ) from e
        except FileNotFoundError as e:
            raise TriageError(
                "claude CLI not found in PATH (install Claude Code or check PATH)"
            ) from e

        if result.returncode != 0:
            raise TriageError(
                f"claude -p failed (exit {result.returncode}): {result.stderr.strip()}"
            )

        if not result.stdout.strip():
            raise TriageError(f"empty response from claude for entry {entry['id']}")

        try:
            envelope = json.loads(result.stdout)
            category = envelope["structured_output"]["category"]
        except (ValueError, KeyError, TypeError) as e:
            raise TriageError(
                f"unexpected claude envelope for entry {entry['id']}: {result.stdout[:200]!r}"
            ) from e
        # スキーマ違反は CLI 側で弾かれる想定の最終防衛線
        if not isinstance(category, str) or category not in SHARD_KINDS:
            raise TriageError(f"invalid shard from claude: {category!r}")
        return category

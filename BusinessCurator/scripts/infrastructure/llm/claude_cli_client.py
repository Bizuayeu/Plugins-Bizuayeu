#!/usr/bin/env python3
"""
ClaudeCliTriageClient
=====================

LLMTriageProtocol の `claude -p` subprocess 実装。

設計意図:
- メモリ「APIキーよりサブスク前提」: Anthropic API 直叩き禁止
- subprocess.run(["claude", "-p", prompt]) で外部 CLI を呼び出し
- レスポンスは 1 行の ShardKind 文字列を期待
- 不正レスポンス・タイムアウト・CLI 不在を TriageError に変換
- テストでは subprocess.run を unittest.mock.patch でスタブ化（CI 互換）
"""

import subprocess

from domain.exceptions import TriageError
from domain.types.entry import RawEntry
from domain.types.shard import SHARD_KINDS, ShardKind

__all__ = ["ClaudeCliTriageClient"]


_DEFAULT_TIMEOUT_SECONDS = 60


_PROMPT_TEMPLATE = """\
Classify the following business email into ONE of these categories:
- projects: project-related emails (specific construction sites, deliverables)
- clients: client-related communications (customers, sales)
- vendors: vendor/supplier communications (purchases, subcontractors)
- knowledge: general knowledge, regulations, standards

Return ONLY the category name (one word, lowercase). No explanation.

Subject: {subject}
From: {from_addr}
Body:
{body}
"""


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
                ["claude", "-p", prompt],
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

        raw_response = result.stdout.strip()
        if not raw_response:
            raise TriageError(f"empty response from claude for entry {entry['id']}")

        normalized = raw_response.lower()
        if normalized not in SHARD_KINDS:
            raise TriageError(
                f"invalid shard from claude: {raw_response!r} (expected one of {SHARD_KINDS})"
            )

        return normalized

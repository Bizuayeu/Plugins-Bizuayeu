#!/usr/bin/env python3
"""
MarkdownAliasResolverRepository
================================

AliasResolverRepositoryProtocol の Markdown ファイル実装。

設計意図:
- 業務計画書 §4.3 のフォーマットに準拠
- セクション分け: ## projects/, ## clients/, ## vendors/, ## knowledge/, ## archive/
- エントリ形式: `- [<canonical>](<target_path>) — also: <a1>, <a2>, ...`
- ファイル不存在時 load_all は空リスト（初回起動状態）
- save_all は常に完全置換

フォーマット例:
    # Global Index

    ## projects/
    - [○○マンション](shards/projects/MaruMaru/_project.md) — also: ○○MS, 2026-003

    ## clients/
    - [株式会社□□](shards/clients/Shikaku.md)

    ## archive/ [archived]
    - [完工：××ビル](archive/projects/Batsu/_project.md) — also: ××
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple

from domain.exceptions import ResolverError
from domain.types.alias import AliasRecord
from domain.types.shard import SHARD_KINDS, ShardKind

__all__ = ["MarkdownAliasResolverRepository"]


# =============================================================================
# Format constants
# =============================================================================

_GLOBAL_INDEX_HEADER = "# Global Index"
_ARCHIVE_SECTION_TITLE = "## archive/ [archived]"

# `- [canonical](target_path) — also: a1, a2`
_ENTRY_RE = re.compile(
    r"^- \[(?P<canonical>[^\]]+)\]\((?P<target>[^)]+)\)(?:\s*[—-]\s*also:\s*(?P<aliases>.+))?$"
)
_SECTION_RE = re.compile(r"^## (?P<kind>[a-z]+)/(?:\s*\[archived\])?\s*$")


class MarkdownAliasResolverRepository:
    """`_alias_resolver.md` への永続化"""

    def __init__(self, file_path: Path) -> None:
        self._path = file_path

    # ------------------------------------------------------------------
    # save_all
    # ------------------------------------------------------------------

    def save_all(self, records: List[AliasRecord]) -> None:
        """
        全レコードを完全置換で書き出し

        Args:
            records: 保存対象
        """
        self._path.parent.mkdir(parents=True, exist_ok=True)

        # シャードごとに振り分け
        active: Dict[ShardKind, List[AliasRecord]] = {k: [] for k in SHARD_KINDS}
        archived: List[AliasRecord] = []
        for r in records:
            if r["archived"]:
                archived.append(r)
            else:
                active[r["shard"]].append(r)

        lines: List[str] = [_GLOBAL_INDEX_HEADER, ""]

        for kind in SHARD_KINDS:
            lines.append(f"## {kind}/")
            for rec in active[kind]:
                lines.append(self._format_entry(rec))
            lines.append("")  # blank line after section

        if archived:
            lines.append(_ARCHIVE_SECTION_TITLE)
            for rec in archived:
                lines.append(self._format_entry(rec))
            lines.append("")

        self._path.write_text("\n".join(lines), encoding="utf-8")

    @staticmethod
    def _format_entry(record: AliasRecord) -> str:
        """1レコードを md 1行に変換"""
        base = f"- [{record['canonical']}]({record['target_path']})"
        if record["aliases"]:
            also = ", ".join(record["aliases"])
            return f"{base} — also: {also}"
        return base

    # ------------------------------------------------------------------
    # load_all
    # ------------------------------------------------------------------

    def load_all(self) -> List[AliasRecord]:
        """
        ファイルから全レコードをロード

        Returns:
            AliasRecord のリスト（ファイル不存在は空リスト）

        Raises:
            ResolverError: パース失敗
        """
        if not self._path.exists():
            return []

        content = self._path.read_text(encoding="utf-8")
        return self._parse(content)

    @classmethod
    def _parse(cls, content: str) -> List[AliasRecord]:
        records: List[AliasRecord] = []
        current_kind: ShardKind | None = None
        current_archived = False

        for raw_line in content.split("\n"):
            line = raw_line.rstrip()
            if not line:
                continue

            # セクションヘッダ
            section_match = _SECTION_RE.match(line)
            if section_match:
                kind_str = section_match.group("kind")
                if kind_str == "archive":
                    current_archived = True
                    current_kind = None
                    continue
                if kind_str in SHARD_KINDS:
                    current_kind = kind_str  # type: ignore[assignment]
                    current_archived = False
                    continue
                continue

            # エントリ
            entry_match = _ENTRY_RE.match(line)
            if not entry_match:
                continue

            canonical = entry_match.group("canonical").strip()
            target = entry_match.group("target").strip()
            aliases_str = entry_match.group("aliases")
            aliases = (
                [a.strip() for a in aliases_str.split(",")] if aliases_str else []
            )

            kind, slug = cls._derive_kind_and_slug(target, current_kind, current_archived)
            records.append(
                {
                    "id": f"{kind}/{slug}",
                    "canonical": canonical,
                    "aliases": aliases,
                    "shard": kind,
                    "target_path": target,
                    "archived": current_archived,
                }
            )
        return records

    @staticmethod
    def _derive_kind_and_slug(
        target_path: str, section_kind: ShardKind | None, archived: bool
    ) -> Tuple[ShardKind, str]:
        """
        target_path から (kind, slug) を導出

        target_path 例:
            shards/projects/MaruMaru/_project.md → (projects, MaruMaru)
            archive/projects/BatsuBatsu/_project.md → (projects, BatsuBatsu)
            shards/clients/Shikaku.md → (clients, Shikaku)
        """
        parts = target_path.replace("\\", "/").split("/")
        # 先頭が "shards" or "archive"
        if len(parts) < 3:
            raise ResolverError(f"cannot derive kind/slug from path: {target_path}")
        # parts[0] = "shards" or "archive"
        kind_str = parts[1]
        if kind_str not in SHARD_KINDS:
            raise ResolverError(f"unknown shard kind in path: {target_path}")
        kind: ShardKind = kind_str  # type: ignore[assignment]

        # slug: ディレクトリ名 or ファイル名 (.md 除去)
        third = parts[2]
        if third.endswith(".md"):
            slug = third[:-3]
        else:
            slug = third
        return kind, slug

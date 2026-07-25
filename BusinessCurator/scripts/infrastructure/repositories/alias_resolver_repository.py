#!/usr/bin/env python3
"""
MarkdownAliasResolverRepository
================================

AliasResolverRepositoryProtocol の Markdown ファイル実装。

設計意図:
- 業務計画書 §4.3 のフォーマットに準拠
- アクティブセクション: ## projects/, ## clients/, ## vendors/, ## knowledge/
- アーカイブセクション (v4 新規): ## archive/<kind>/ [completed], ## archive/<kind>/ [removed]
- エントリ形式: `- [<canonical>](<target_path>) — also: <a1>, <a2>, ...`
- ファイル不存在時 load_all は空リスト（初回起動状態）
- save_all は常に完全置換

フォーマット例:
    # Global Index

    ## projects/
    - [○○マンション](shards/projects/MaruMaru/_project.md) — also: ○○MS, 2026-003

    ## clients/
    - [株式会社□□](shards/clients/Shikaku.md)

    ## archive/projects/ [completed]
    - [完工：墨田区向島](archive/projects/MukojimaSumida/_project.md) — also: 向島案件

    ## archive/vendors/ [removed]
    - [yamaguchi-ind.co.jp](shards/vendors/YamaguchiInd.md) — also: yamaguchi-ind.co.jp
"""

import re
from pathlib import Path
from typing import Dict, List, Literal, Tuple

from domain.exceptions import ResolverError
from domain.types.alias import AliasRecord
from domain.types.shard import SHARD_KINDS, ArchiveStatus, ShardKind

__all__ = ["MarkdownAliasResolverRepository"]


# =============================================================================
# Format constants
# =============================================================================

_GLOBAL_INDEX_HEADER = "# Global Index"

# `- [canonical](target_path) — also: a1, a2`
_ENTRY_RE = re.compile(
    r"^- \[(?P<canonical>[^\]]+)\]\((?P<target>[^)]+)\)(?:\s*[—-]\s*also:\s*(?P<aliases>.+))?$"
)

# アクティブセクション: ## projects/, ## clients/, ...
_ACTIVE_SECTION_RE = re.compile(r"^## (?P<kind>[a-z]+)/\s*$")

# アーカイブセクション: ## archive/projects/ [completed], ## archive/vendors/ [removed]
_ARCHIVE_COMPLETED_RE = re.compile(r"^## archive/(?P<kind>[a-z]+)/\s*\[completed\]\s*$")
_ARCHIVE_REMOVED_RE = re.compile(r"^## archive/(?P<kind>[a-z]+)/\s*\[removed\]\s*$")

_SectionMode = Literal["active", "completed", "removed"]


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

        Note:
            3 状態で振り分けて書き出す:
              - active:    ## <kind>/
              - completed: ## archive/<kind>/ [completed]
              - removed:   ## archive/<kind>/ [removed]
        """
        self._path.parent.mkdir(parents=True, exist_ok=True)

        # 3 状態 × 4 シャードで振り分け
        active: Dict[ShardKind, List[AliasRecord]] = {k: [] for k in SHARD_KINDS}
        completed: Dict[ShardKind, List[AliasRecord]] = {k: [] for k in SHARD_KINDS}
        removed: Dict[ShardKind, List[AliasRecord]] = {k: [] for k in SHARD_KINDS}

        for r in records:
            status = r["archive_status"]
            if status == "active":
                active[r["shard"]].append(r)
            elif status == "completed":
                completed[r["shard"]].append(r)
            elif status == "removed":
                removed[r["shard"]].append(r)

        lines: List[str] = [_GLOBAL_INDEX_HEADER, ""]

        # アクティブセクション (4 シャード)
        for kind in SHARD_KINDS:
            lines.append(f"## {kind}/")
            for rec in active[kind]:
                lines.append(self._format_entry(rec))
            lines.append("")

        # completed セクション (存在する kind のみ)
        for kind in SHARD_KINDS:
            if completed[kind]:
                lines.append(f"## archive/{kind}/ [completed]")
                for rec in completed[kind]:
                    lines.append(self._format_entry(rec))
                lines.append("")

        # removed セクション (存在する kind のみ)
        for kind in SHARD_KINDS:
            if removed[kind]:
                lines.append(f"## archive/{kind}/ [removed]")
                for rec in removed[kind]:
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
        current_mode: _SectionMode = "active"

        for raw_line in content.split("\n"):
            line = raw_line.rstrip()
            if not line:
                continue

            # アーカイブ [completed] セクション
            completed_match = _ARCHIVE_COMPLETED_RE.match(line)
            if completed_match:
                kind_str = completed_match.group("kind")
                if kind_str in SHARD_KINDS:
                    current_kind = kind_str
                    current_mode = "completed"
                else:
                    current_kind = None
                continue

            # アーカイブ [removed] セクション
            removed_match = _ARCHIVE_REMOVED_RE.match(line)
            if removed_match:
                kind_str = removed_match.group("kind")
                if kind_str in SHARD_KINDS:
                    current_kind = kind_str
                    current_mode = "removed"
                else:
                    current_kind = None
                continue

            # アクティブセクション (## <kind>/)
            active_match = _ACTIVE_SECTION_RE.match(line)
            if active_match:
                kind_str = active_match.group("kind")
                if kind_str in SHARD_KINDS:
                    current_kind = kind_str
                    current_mode = "active"
                else:
                    current_kind = None
                continue

            # エントリ
            entry_match = _ENTRY_RE.match(line)
            if not entry_match:
                continue

            canonical = entry_match.group("canonical").strip()
            target = entry_match.group("target").strip()
            aliases_str = entry_match.group("aliases")
            aliases = [a.strip() for a in aliases_str.split(",")] if aliases_str else []

            kind, slug = cls._derive_kind_and_slug(target, current_kind)
            status: ArchiveStatus = current_mode
            records.append(
                {
                    "id": f"{kind}/{slug}",
                    "canonical": canonical,
                    "aliases": aliases,
                    "shard": kind,
                    "target_path": target,
                    "archive_status": status,
                }
            )
        return records

    @staticmethod
    def _derive_kind_and_slug(
        target_path: str, section_kind: ShardKind | None
    ) -> Tuple[ShardKind, str]:
        """
        target_path から (kind, slug) を導出

        target_path 例:
            shards/projects/MaruMaru/_project.md → (projects, MaruMaru)
            archive/projects/BatsuBatsu/_project.md → (projects, BatsuBatsu)
            shards/clients/Shikaku.md → (clients, Shikaku)
        """
        parts = target_path.replace("\\", "/").split("/")
        if len(parts) < 3:
            raise ResolverError(f"cannot derive kind/slug from path: {target_path}")
        kind_str = parts[1]
        if kind_str not in SHARD_KINDS:
            raise ResolverError(f"unknown shard kind in path: {target_path}")
        kind: ShardKind = kind_str

        third = parts[2]
        if third.endswith(".md"):
            slug = third[:-3]
        else:
            slug = third
        return kind, slug

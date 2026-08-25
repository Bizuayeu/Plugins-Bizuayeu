#!/usr/bin/env python3
"""
Migration: archived bool → archive_status enum
===============================================

v3 の `## archive/ [archived]` セクションを v4 の
`## archive/<kind>/ [completed]` / `## archive/<kind>/ [removed]` に変換する。

分類ロジック:
- target_path が "archive/" 始まり → archive_status = "completed"
- それ以外（"shards/" 等） → archive_status = "removed"

一発実行の片道変換。idempotent 保証は不要。
"""

import re
from pathlib import Path

from domain.types.alias import AliasRecord
from domain.types.shard import SHARD_KINDS, ArchiveStatus, ShardKind
from infrastructure.repositories.alias_resolver_repository import (
    MarkdownAliasResolverRepository,
)

__all__ = ["migrate"]

_OLD_ARCHIVE_SECTION_RE = re.compile(r"^## archive/\s*\[archived\]\s*$")
_ACTIVE_SECTION_RE = re.compile(r"^## (?P<kind>[a-z]+)/\s*$")
_ENTRY_RE = re.compile(
    r"^- \[(?P<canonical>[^\]]+)\]\((?P<target>[^)]+)\)(?:\s*[—-]\s*also:\s*(?P<aliases>.+))?$"
)


def _parse_old_format(content: str) -> list[AliasRecord]:
    """v3 旧フォーマットをパースして AliasRecord リストを返す"""
    records: list[AliasRecord] = []
    in_old_archive = False

    for raw_line in content.split("\n"):
        line = raw_line.rstrip()
        if not line:
            continue

        if _OLD_ARCHIVE_SECTION_RE.match(line):
            in_old_archive = True
            continue

        active_match = _ACTIVE_SECTION_RE.match(line)
        if active_match:
            kind_str = active_match.group("kind")
            if kind_str in SHARD_KINDS:
                in_old_archive = False
            continue

        entry_match = _ENTRY_RE.match(line)
        if not entry_match:
            continue

        canonical = entry_match.group("canonical").strip()
        target = entry_match.group("target").strip()
        aliases_str = entry_match.group("aliases")
        aliases = [a.strip() for a in aliases_str.split(",")] if aliases_str else []

        kind, slug = _derive_kind_and_slug(target)

        status: ArchiveStatus
        if in_old_archive:
            status = "completed" if target.startswith("archive/") else "removed"
        else:
            status = "active"

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


def _derive_kind_and_slug(target_path: str) -> tuple[ShardKind, str]:
    parts = target_path.replace("\\", "/").split("/")
    if len(parts) < 3:
        raise ValueError(f"cannot derive kind/slug from path: {target_path}")
    kind_str = parts[1]
    if kind_str not in SHARD_KINDS:
        raise ValueError(f"unknown shard kind in path: {target_path}")
    kind: ShardKind = kind_str
    third = parts[2]
    slug = third[:-3] if third.endswith(".md") else third
    return kind, slug


def migrate(plugin_root: Path, *, dry_run: bool = False) -> str:
    """
    旧フォーマット → 新フォーマットへの migration 実行

    Args:
        plugin_root: BusinessWiki ルートディレクトリ
        dry_run: True の場合は変換結果を表示するのみ

    Returns:
        Markdown 形式のレポート文字列
    """
    resolver_path = plugin_root / "_alias_resolver.md"
    if not resolver_path.exists():
        return (
            "## Migration Report\n\n_alias_resolver.md not found. Nothing to migrate."
        )

    old_content = resolver_path.read_text(encoding="utf-8")

    if "## archive/" not in old_content or "[archived]" not in old_content:
        return "## Migration Report\n\nNo old-format archive section found. Already migrated or no archived records."

    records = _parse_old_format(old_content)

    active = [r for r in records if r["archive_status"] == "active"]
    completed = [r for r in records if r["archive_status"] == "completed"]
    removed = [r for r in records if r["archive_status"] == "removed"]

    report_lines = [
        "## Migration Report",
        "",
        f"- Total records: {len(records)}",
        f"- Active: {len(active)}",
        f"- Completed: {len(completed)}",
        f"- Removed: {len(removed)}",
        "",
    ]

    if completed:
        report_lines.append("### Completed (target_path starts with archive/)")
        for r in completed:
            report_lines.append(f"- {r['id']}: {r['target_path']}")
        report_lines.append("")

    if removed:
        report_lines.append("### Removed (logical delete, target_path unchanged)")
        for r in removed:
            report_lines.append(f"- {r['id']}: {r['target_path']}")
        report_lines.append("")

    if dry_run:
        report_lines.append("**DRY RUN** — no changes written.")
    else:
        repo = MarkdownAliasResolverRepository(file_path=resolver_path)
        repo.save_all(records)
        report_lines.append(f"**DONE** — {resolver_path} updated to new format.")

    return "\n".join(report_lines)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Migrate _alias_resolver.md to archive_status format"
    )
    parser.add_argument(
        "--plugin-root", required=True, help="BusinessWiki root directory"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview without writing"
    )
    args = parser.parse_args()

    report = migrate(Path(args.plugin_root), dry_run=args.dry_run)
    print(report)


if __name__ == "__main__":
    main()

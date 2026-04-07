#!/usr/bin/env python3
"""
archive_cli
===========

案件アーカイブの CLI。

サブコマンド:
- plan:    manifest 生成のみ（resolver 非更新、ファイル非移動）
- execute: resolver 更新 + ファイル移動（--no-move でスキップ）

JSON 出力スキーマ:
    plan:    {"status": "ok", "action": "plan", "manifest": {...}}
    execute: {"status": "ok", "action": "execute", "manifest": {...}, "moved": <bool>}

Composition Root:
    PathResolver
      → MarkdownAliasResolverRepository → ResolverService
      → SystemClock
      → ArchiveOrchestrator
"""

import argparse
import shutil
import sys
from pathlib import Path
from typing import List, Optional

from application.archive.archive_orchestrator import ArchiveOrchestrator
from application.resolver.resolver_service import ResolverService
from domain.exceptions import (
    ArchiveError,
    BusinessCuratorError,
    EntityNotFoundError,
)
from infrastructure.clock import SystemClock
from infrastructure.path_resolver import PathResolver
from infrastructure.repositories.alias_resolver_repository import (
    MarkdownAliasResolverRepository,
)
from interfaces.cli_helpers import output_error, output_json

__all__ = ["main"]


# =============================================================================
# Composition Root
# =============================================================================


def _make_orchestrator(plugin_root: Path) -> tuple[ArchiveOrchestrator, PathResolver]:
    resolver = PathResolver(plugin_root)
    alias_repo = MarkdownAliasResolverRepository(file_path=resolver.alias_resolver_path)
    svc = ResolverService(alias_repo)
    clock = SystemClock()
    return ArchiveOrchestrator(resolver_service=svc, clock=clock), resolver


# =============================================================================
# argparse
# =============================================================================


def _add_common(p: argparse.ArgumentParser) -> None:
    p.add_argument("--plugin-root", required=True)
    p.add_argument("--project", required=True, help="Project slug to archive")
    p.add_argument("--reason", default="completed", help="Archive reason")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m interfaces.archive_cli",
        description="Archive a project (manifest + resolver update + file move)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_plan = sub.add_parser("plan", help="Build manifest only (no side effects)")
    _add_common(p_plan)

    p_exec = sub.add_parser("execute", help="Update resolver and move files")
    _add_common(p_exec)
    p_exec.add_argument(
        "--no-move",
        action="store_true",
        help="Skip filesystem move (resolver update only)",
    )

    return parser


# =============================================================================
# move helper
# =============================================================================


def _move_directory(source: Path, destination: Path) -> None:
    """source ディレクトリを destination に移動

    Raises:
        FileNotFoundError: source が存在しない
        FileExistsError: destination が既に存在
    """
    if not source.exists():
        raise FileNotFoundError(f"source not found: {source}")
    if destination.exists():
        raise FileExistsError(f"destination already exists: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source), str(destination))


# =============================================================================
# main
# =============================================================================


def main(argv: Optional[List[str]] = None) -> int:
    args = _build_parser().parse_args(argv)
    plugin_root = Path(args.plugin_root)
    orch, resolver = _make_orchestrator(plugin_root)

    try:
        if args.command == "plan":
            manifest = orch.create_manifest(args.project, reason=args.reason)
            output_json({"status": "ok", "action": "plan", "manifest": manifest})
            return 0

        # execute
        manifest = orch.execute(args.project, reason=args.reason)
        moved = False
        if not args.no_move:
            try:
                _move_directory(
                    plugin_root / manifest["source_path"],
                    plugin_root / manifest["destination_path"],
                )
                moved = True
            except (FileNotFoundError, FileExistsError) as e:
                # 移動失敗してもマニフェストは生成済みなので警告 + 詳細
                output_error(
                    f"move failed: {e}",
                    details={"manifest": dict(manifest)},
                )
        output_json(
            {
                "status": "ok",
                "action": "execute",
                "manifest": manifest,
                "moved": moved,
            }
        )
        return 0

    except EntityNotFoundError as e:
        output_error(f"not found: {e}")
    except ArchiveError as e:
        output_error(f"archive error: {e}")
    except BusinessCuratorError as e:
        output_error(f"failed: {e}")


if __name__ == "__main__":
    sys.exit(main())

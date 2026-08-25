#!/usr/bin/env python3
"""
index_cli
=========

`_index.md` ツリー再生成 CLI。

サブコマンド:
- rebuild: ルート + 全シャード（または指定シャードのみ）の _index.md を再生成

JSON 出力スキーマ:
    rebuild (all):   {"status": "ok", "action": "rebuild_all", "counts": {"projects": N, ...}}
    rebuild (shard): {"status": "ok", "action": "rebuild_shard", "shard": <kind>, "count": N}

Composition Root:
    PathResolver → MarkdownAliasResolverRepository → ResolverService
    + IndexFileRepository + IndexMarkdownFormatter → IndexGeneratorService
"""

import argparse
import sys
from pathlib import Path

from application.indexing.index_generator_service import IndexGeneratorService
from application.resolver.resolver_service import ResolverService
from domain.exceptions import BusinessCuratorError
from domain.types.shard import SHARD_KINDS
from infrastructure.path_resolver import PathResolver
from infrastructure.repositories.alias_resolver_repository import (
    MarkdownAliasResolverRepository,
)
from infrastructure.repositories.index_file_repository import IndexFileRepository
from interfaces.cli_helpers import output_error, output_json
from interfaces.formatters.index_markdown_formatter import IndexMarkdownFormatter

__all__ = ["main", "make_service"]


# =============================================================================
# Composition Root
# =============================================================================


def make_service(plugin_root: Path) -> IndexGeneratorService:
    """
    IndexGeneratorService を全依存注入で組み立てる。

    resolver_cli など他 CLI からの自動トリガーでも再利用する公開関数。
    """
    resolver_paths = PathResolver(plugin_root)
    alias_repo = MarkdownAliasResolverRepository(
        file_path=resolver_paths.alias_resolver_path
    )
    resolver_svc = ResolverService(alias_repo)
    file_repo = IndexFileRepository(plugin_root)
    formatter = IndexMarkdownFormatter()
    return IndexGeneratorService(resolver_svc, file_repo, formatter)


# =============================================================================
# argparse
# =============================================================================


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m interfaces.index_cli",
        description="Regenerate BusinessWiki _index.md tree",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_rebuild = sub.add_parser("rebuild", help="Regenerate _index.md files")
    p_rebuild.add_argument("--plugin-root", required=True)
    p_rebuild.add_argument(
        "--shard",
        default="all",
        choices=["all", *SHARD_KINDS],
        help="Target shard (default: all)",
    )
    p_rebuild.add_argument(
        "--include-archived",
        action="store_true",
        help="Include archived records in the output",
    )

    return parser


# =============================================================================
# handlers
# =============================================================================


def _handle_rebuild(service: IndexGeneratorService, args: argparse.Namespace) -> None:
    if args.shard == "all":
        counts = service.regenerate_all(include_archived=args.include_archived)
        output_json({"status": "ok", "action": "rebuild_all", "counts": counts})
    else:
        count = service.regenerate_shard(args.shard)
        output_json(
            {
                "status": "ok",
                "action": "rebuild_shard",
                "shard": args.shard,
                "count": count,
            }
        )


# =============================================================================
# main
# =============================================================================


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    service = make_service(Path(args.plugin_root))
    try:
        if args.command == "rebuild":
            _handle_rebuild(service, args)
        else:  # pragma: no cover - argparse で弾かれる
            output_error(f"unknown command: {args.command}")
    except BusinessCuratorError as e:
        output_error(f"failed: {e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

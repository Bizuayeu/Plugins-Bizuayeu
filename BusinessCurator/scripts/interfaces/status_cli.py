#!/usr/bin/env python3
"""
status_cli
==========

シャード横断のステータスメトリクスを集計して JSON 出力する CLI。

JSON 出力スキーマ:
    {
        "status": "ok",
        "metrics": {
            "raw_entries_count": <int>,
            "alias_records_total": <int>,
            "alias_records_active": <int>,
            "alias_records_archived": <int>,
            "alias_per_shard": {"projects": <int>, ...},
            "unclassified_count": <int>
        }
    }

Composition Root:
    PathResolver
      → FileEntryRepository
      → MarkdownAliasResolverRepository
      → unclassified_count_provider (lambda: count of inbox/unclassified/*.md)
      → MetricsCollectorUseCase
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from application.status.metrics_collector import MetricsCollectorUseCase
from infrastructure.path_resolver import PathResolver
from infrastructure.repositories.alias_resolver_repository import (
    MarkdownAliasResolverRepository,
)
from infrastructure.repositories.entry_repository import FileEntryRepository
from interfaces.cli_helpers import output_json

__all__ = ["main"]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m interfaces.status_cli",
        description="Collect cross-shard status metrics",
    )
    parser.add_argument("--plugin-root", required=True)
    return parser


def _count_unclassified(directory: Path) -> int:
    if not directory.exists():
        return 0
    return sum(1 for p in directory.iterdir() if p.is_file() and not p.name.startswith("."))


def main(argv: Optional[List[str]] = None) -> int:
    args = _build_parser().parse_args(argv)
    plugin_root = Path(args.plugin_root)
    resolver = PathResolver(plugin_root)

    entry_repo = FileEntryRepository(raw_entries_dir=resolver.raw_entries_dir)
    alias_repo = MarkdownAliasResolverRepository(file_path=resolver.alias_resolver_path)

    usecase = MetricsCollectorUseCase(
        entry_repository=entry_repo,
        alias_repository=alias_repo,
        unclassified_count_provider=lambda: _count_unclassified(resolver.unclassified_dir),
    )

    metrics = usecase.execute()
    output_json({"status": "ok", "metrics": metrics.to_dict()})
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
ingest_cli
==========

ingest CLI: メールファイルから RawEntry を生成して raw-entries/ に保存。

Composition Root:
- format_detector → EmlEmailParser / MboxEmailParser
- ParseEmailUseCase + FileEntryRepository を IngestBatchUseCase に注入

Usage:
    python -m interfaces.ingest_cli --source <path> --plugin-root <path>

Output (JSON):
    {
        "status": "ok",
        "saved": 5,
        "skipped": 0,
        "failed": 0,
        "total": 5
    }
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from application.ingest.ingest_batch import IngestBatchUseCase
from application.ingest.parse_email import ParseEmailUseCase
from domain.exceptions import BusinessCuratorError
from infrastructure.email_parser.eml_parser import EmlEmailParser
from infrastructure.email_parser.format_detector import EmailFormat, detect_email_format
from infrastructure.email_parser.mbox_parser import MboxEmailParser
from infrastructure.path_resolver import PathResolver
from infrastructure.repositories.entry_repository import FileEntryRepository
from interfaces.cli_helpers import output_error, output_json

__all__ = ["main"]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m interfaces.ingest_cli",
        description="Ingest email files (.eml/.mbox) into raw-entries/",
    )
    parser.add_argument(
        "--source",
        required=True,
        help="Path to .eml or .mbox file (extension or signature auto-detected)",
    )
    parser.add_argument(
        "--plugin-root",
        required=True,
        help="Plugin root directory (raw-entries/ will be created if missing)",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """
    Entry point

    Args:
        argv: コマンドライン引数（None の場合は sys.argv[1:]）

    Returns:
        exit code (0 for success, 1 for error)
    """
    args = _build_parser().parse_args(argv)
    source = Path(args.source)
    plugin_root = Path(args.plugin_root)

    if not source.exists():
        output_error(
            f"source not found: {source}",
            details={"action": "verify the path"},
        )

    try:
        email_format = detect_email_format(source)
    except (ValueError, FileNotFoundError, IsADirectoryError) as e:
        output_error(f"format detection failed: {e}")

    parser: EmlEmailParser | MboxEmailParser
    if email_format == EmailFormat.EML:
        parser = EmlEmailParser()
    else:
        parser = MboxEmailParser()

    resolver = PathResolver(plugin_root)
    repo = FileEntryRepository(raw_entries_dir=resolver.raw_entries_dir)
    parse_uc = ParseEmailUseCase()
    usecase = IngestBatchUseCase(email_parser=parser, parse_usecase=parse_uc, entry_repository=repo)

    try:
        result = usecase.execute(source)
    except BusinessCuratorError as e:
        output_error(f"ingest failed: {e}")

    output_json({"status": "ok", **result.to_dict()})
    return 0


if __name__ == "__main__":
    sys.exit(main())

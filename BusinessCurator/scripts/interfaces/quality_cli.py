#!/usr/bin/env python3
"""
quality_cli
===========

品質検証 CLI。wikilink の整合性チェックを実行する。

サブコマンド:
- verify-wikilinks: shards/ 配下の Markdown から [[kind/Slug]] を抽出し resolver と突合

JSON 出力スキーマ:
    {
        "status": "ok",
        "total_links": <int>,
        "valid": <int>,
        "broken_count": <int>,
        "stale_count": <int>,
        "broken": [{"file": <str>, "link": <str>}, ...],
        "stale": [{"file": <str>, "link": <str>}, ...]
    }

Composition Root:
    PathResolver → MarkdownAliasResolverRepository → ResolverService → WikilinkVerifier
"""

import argparse
import re
import sys
from pathlib import Path

from application.quality.wikilink_verifier import WikilinkVerifier
from application.resolver.resolver_service import ResolverService
from infrastructure.path_resolver import PathResolver
from infrastructure.repositories.alias_resolver_repository import (
    MarkdownAliasResolverRepository,
)
from interfaces.cli_helpers import output_error, output_json

__all__ = ["main"]

_WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")


def _make_verifier(plugin_root: Path) -> WikilinkVerifier:
    resolver = PathResolver(plugin_root)
    repo = MarkdownAliasResolverRepository(file_path=resolver.alias_resolver_path)
    svc = ResolverService(repo)
    return WikilinkVerifier(svc)


def _scan_wikilinks(plugin_root: Path) -> list[tuple[str, str]]:
    """shards/ と archive/ 配下の .md ファイルから [[...]] を抽出"""
    links: list[tuple[str, str]] = []
    for search_dir in [plugin_root / "shards", plugin_root / "archive"]:
        if not search_dir.exists():
            continue
        for md_file in search_dir.rglob("*.md"):
            if md_file.name.startswith("_"):
                continue
            try:
                content = md_file.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            rel_path = str(md_file.relative_to(plugin_root)).replace("\\", "/")
            for match in _WIKILINK_RE.finditer(content):
                link_target = match.group(1).strip()
                links.append((rel_path, link_target))
    return links


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m interfaces.quality_cli",
        description="Quality verification commands",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_verify = sub.add_parser(
        "verify-wikilinks", help="Verify wikilinks against resolver"
    )
    p_verify.add_argument("--plugin-root", required=True)

    return parser


def _handle_verify_wikilinks(args: argparse.Namespace) -> None:
    plugin_root = Path(args.plugin_root)
    verifier = _make_verifier(plugin_root)
    links = _scan_wikilinks(plugin_root)
    result = verifier.verify_links(links)
    output_json({"status": "ok", **result.to_dict()})


_HANDLERS = {
    "verify-wikilinks": _handle_verify_wikilinks,
}


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    handler = _HANDLERS[args.command]
    try:
        handler(args)
    except Exception as e:
        output_error(str(e))
    return 0


if __name__ == "__main__":
    sys.exit(main())

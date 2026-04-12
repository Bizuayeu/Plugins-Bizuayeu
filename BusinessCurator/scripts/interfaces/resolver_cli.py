#!/usr/bin/env python3
"""
resolver_cli
============

エイリアスリゾルバ CRUD CLI。

サブコマンド:
- add:    新規エントリ追加
- edit:   既存エントリ部分更新
- remove: 論理削除（archive_status = "removed"）
- list:   一覧（デフォルトは active のみ）
- find:   ID で検索

JSON 出力スキーマ:
    add/edit/remove: {"status": "ok", "action": <action>, "id": <id>}
    list:            {"status": "ok", "count": <int>, "records": [<AliasRecord>, ...]}
    find:            {"status": "ok", "record": <AliasRecord>}

Composition Root:
    PathResolver → MarkdownAliasResolverRepository → ResolverService
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from application.resolver.resolver_service import ResolverService
from domain.exceptions import (
    BusinessCuratorError,
    EntityNotFoundError,
    ResolverError,
)
from domain.types.alias import AliasRecord
from domain.types.shard import SHARD_KINDS
from infrastructure.path_resolver import PathResolver
from infrastructure.repositories.alias_resolver_repository import (
    MarkdownAliasResolverRepository,
)
from interfaces.cli_helpers import output_error, output_json

__all__ = ["main"]


# =============================================================================
# Auto trigger: `_index.md` ツリー再生成
# =============================================================================


def _rebuild_index(plugin_root_str: str) -> None:
    """
    alias resolver の変更後に呼ぶ `_index.md` 再生成フック。

    ここで index_cli を import することで、軽量なテストで resolver_cli のみを
    動かすケースでも indexing 依存を強制しない（遅延 import）。
    """
    from interfaces.index_cli import make_service as _make_index_service

    _make_index_service(Path(plugin_root_str)).regenerate_all()


def _should_skip_rebuild(args: argparse.Namespace) -> bool:
    return bool(getattr(args, "skip_index_rebuild", False))


# =============================================================================
# Composition Root
# =============================================================================


def _make_service(plugin_root: Path) -> ResolverService:
    resolver = PathResolver(plugin_root)
    repo = MarkdownAliasResolverRepository(file_path=resolver.alias_resolver_path)
    return ResolverService(repo)


# =============================================================================
# argparse
# =============================================================================


def _add_plugin_root(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--plugin-root",
        required=True,
        help="Plugin root directory",
    )


def _add_skip_index_rebuild(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--skip-index-rebuild",
        action="store_true",
        dest="skip_index_rebuild",
        help="Suppress automatic _index.md regeneration (batch operations)",
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m interfaces.resolver_cli",
        description="Manage alias resolver records (CRUD)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # add
    p_add = sub.add_parser("add", help="Add a new alias record")
    _add_plugin_root(p_add)
    _add_skip_index_rebuild(p_add)
    p_add.add_argument("--kind", required=True, choices=list(SHARD_KINDS))
    p_add.add_argument("--slug", required=True)
    p_add.add_argument("--canonical", required=True)
    p_add.add_argument("--target-path", required=True)
    p_add.add_argument(
        "--aliases",
        default="",
        help='Comma-separated aliases (e.g. "alias1,alias2")',
    )

    # edit
    p_edit = sub.add_parser("edit", help="Edit an existing alias record")
    _add_plugin_root(p_edit)
    _add_skip_index_rebuild(p_edit)
    p_edit.add_argument("--id", required=True, dest="record_id")
    p_edit.add_argument("--canonical", default=None)
    p_edit.add_argument("--target-path", default=None)
    p_edit.add_argument("--add-aliases", default="", dest="add_aliases")
    p_edit.add_argument("--remove-aliases", default="", dest="remove_aliases")

    # remove
    p_rm = sub.add_parser("remove", help="Logically remove (archive) an alias record")
    _add_plugin_root(p_rm)
    _add_skip_index_rebuild(p_rm)
    p_rm.add_argument("--id", required=True, dest="record_id")

    # list
    p_list = sub.add_parser("list", help="List alias records")
    _add_plugin_root(p_list)
    p_list.add_argument("--include-archived", action="store_true")
    p_list.add_argument("--shard", default=None, choices=list(SHARD_KINDS))

    # find
    p_find = sub.add_parser("find", help="Find an alias record by id")
    _add_plugin_root(p_find)
    p_find.add_argument("--id", required=True, dest="record_id")

    return parser


# =============================================================================
# サブコマンドハンドラ
# =============================================================================


def _split_csv(value: str) -> List[str]:
    if not value.strip():
        return []
    return [s.strip() for s in value.split(",") if s.strip()]


def _handle_add(svc: ResolverService, args: argparse.Namespace) -> None:
    record: AliasRecord = {
        "id": f"{args.kind}/{args.slug}",
        "canonical": args.canonical,
        "aliases": _split_csv(args.aliases),
        "shard": args.kind,
        "target_path": args.target_path,
        "archive_status": "active",
    }
    svc.add(record)
    if not _should_skip_rebuild(args):
        _rebuild_index(args.plugin_root)
    output_json({"status": "ok", "action": "add", "id": record["id"]})


def _handle_edit(svc: ResolverService, args: argparse.Namespace) -> None:
    svc.edit(
        args.record_id,
        canonical=args.canonical,
        target_path=args.target_path,
        add_aliases=_split_csv(args.add_aliases) or None,
        remove_aliases=_split_csv(args.remove_aliases) or None,
    )
    if not _should_skip_rebuild(args):
        _rebuild_index(args.plugin_root)
    output_json({"status": "ok", "action": "edit", "id": args.record_id})


def _handle_remove(svc: ResolverService, args: argparse.Namespace) -> None:
    svc.remove(args.record_id)
    if not _should_skip_rebuild(args):
        _rebuild_index(args.plugin_root)
    output_json({"status": "ok", "action": "remove", "id": args.record_id})


def _handle_list(svc: ResolverService, args: argparse.Namespace) -> None:
    if args.include_archived:
        records: List[AliasRecord] = list(
            svc._repo.load_all()  # noqa: SLF001 (CLI 経由のインスペクション)
        )
    else:
        records = svc.list_active()

    if args.shard is not None:
        records = [r for r in records if r["shard"] == args.shard]

    output_json(
        {
            "status": "ok",
            "count": len(records),
            "records": records,
        }
    )


def _handle_find(svc: ResolverService, args: argparse.Namespace) -> None:
    record = svc.find(args.record_id)
    output_json({"status": "ok", "record": record})


_HANDLERS = {
    "add": _handle_add,
    "edit": _handle_edit,
    "remove": _handle_remove,
    "list": _handle_list,
    "find": _handle_find,
}


# =============================================================================
# main
# =============================================================================


def main(argv: Optional[List[str]] = None) -> int:
    args = _build_parser().parse_args(argv)
    svc = _make_service(Path(args.plugin_root))
    handler = _HANDLERS[args.command]
    try:
        handler(svc, args)
    except EntityNotFoundError as e:
        output_error(f"not found: {e}", details={"id": getattr(args, "record_id", None)})
    except ResolverError as e:
        output_error(f"resolver error: {e}")
    except BusinessCuratorError as e:
        output_error(f"failed: {e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

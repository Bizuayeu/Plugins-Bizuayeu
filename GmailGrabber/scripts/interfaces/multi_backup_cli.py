#!/usr/bin/env python3
"""
multi_backup_cli
================

複数ユーザー Gmail バックアップ CLI (Service Account + Domain-Wide Delegation 版)。

Usage:
    PYTHONPATH=scripts python -m interfaces.multi_backup_cli \
        --service-account-key PATH \
        (--impersonate-users a@d.com,b@d.com | --impersonate-users-file users.txt) \
        --output-dir PATH \
        [--format eml|mbox] \
        [--after YYYY/MM/DD] [--before YYYY/MM/DD] \
        [--from-addr ADDR] [--subject TEXT] [--label NAME] \
        [--has-attachment] [--raw-query "q"] \
        [--max-messages-per-user N] \
        [--no-resume] \
        [--state-dir PATH] [--config-dir PATH]
"""

import argparse
from pathlib import Path

from application.fetch.multi_user_fetch_batch import MultiUserFetchBatchUseCase
from domain.constants import (
    DEFAULT_SCOPES,
    OUTPUT_FORMAT_EML,
    VALID_OUTPUT_FORMATS,
)
from domain.multi_file_naming import build_multi_plan_id
from domain.protocols import MessageWriterProtocol
from domain.query_builder import build_gmail_query
from domain.types.account import GmailAccount
from domain.types.multi_backup import MultiUserBackupPlan
from infrastructure.clock import SystemClock
from infrastructure.google_gmail.gmail_client_factory import GoogleGmailClientFactory
from infrastructure.repositories.json_multi_user_state_repository import (
    JsonMultiUserStateRepository,
)
from infrastructure.writers.eml_writer import EmlFileWriter
from infrastructure.writers.mbox_writer import MboxFileWriter
from interfaces.backup_cli import _build_search_query, _parse_date
from interfaces.cli_helpers import default_config_dir, fail, print_success

# Re-export to silence "unused import" linters while keeping referential docs:
_ = _parse_date


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="gmailgrabber-multi-backup",
        description=(
            "Backup Gmail messages from multiple Workspace users via "
            "Service Account impersonation with Message-ID deduplication."
        ),
    )
    p.add_argument("--service-account-key", required=True, help="Path to SA JSON key")
    users_group = p.add_mutually_exclusive_group(required=True)
    users_group.add_argument(
        "--impersonate-users",
        help="Comma-separated user emails to impersonate",
    )
    users_group.add_argument(
        "--impersonate-users-file",
        help="File with one user email per line",
    )
    p.add_argument("--output-dir", required=True)
    p.add_argument("--format", choices=VALID_OUTPUT_FORMATS, default=OUTPUT_FORMAT_EML)
    p.add_argument("--after", help="YYYY/MM/DD (inclusive)")
    p.add_argument("--before", help="YYYY/MM/DD (exclusive)")
    p.add_argument("--from-addr", dest="from_addr")
    p.add_argument("--to-addr", dest="to_addr")
    p.add_argument("--subject")
    p.add_argument("--label")
    p.add_argument("--has-attachment", action="store_true")
    p.add_argument("--raw-query", dest="raw_query")
    p.add_argument("--max-messages-per-user", type=int, default=None)
    p.add_argument("--no-resume", dest="resume", action="store_false")
    p.add_argument("--state-dir", default=None)
    p.add_argument("--config-dir", default=None)
    return p


def _load_users(args: argparse.Namespace) -> list[str]:
    if args.impersonate_users:
        return [e.strip() for e in args.impersonate_users.split(",") if e.strip()]
    path = Path(args.impersonate_users_file)
    if not path.exists():
        fail(f"users file not found: {args.impersonate_users_file}")
    lines = path.read_text(encoding="utf-8").splitlines()
    return [
        line.strip()
        for line in lines
        if line.strip() and not line.strip().startswith("#")
    ]


def _build_accounts(user_emails: list[str], config_dir: Path) -> list[GmailAccount]:
    accounts: list[GmailAccount] = []
    for email in user_emails:
        label = email.split("@")[0]
        accounts.append(
            {
                "email": email,
                "label": label,
                "credentials_path": "",  # Service Account 経路では未使用
                "token_path": str(config_dir / f"token_{label}.json"),
            }
        )
    return accounts


def _make_writer(output_format: str, multi_plan_id: str) -> MessageWriterProtocol:
    if output_format == "eml":
        return EmlFileWriter()
    if output_format == "mbox":
        return MboxFileWriter(plan_id=multi_plan_id)
    raise ValueError(f"unsupported format: {output_format}")


def main(argv: list[str] | None = None) -> None:
    args = _build_parser().parse_args(argv)

    config_dir = (
        Path(args.config_dir).expanduser() if args.config_dir else default_config_dir()
    )
    config_dir.mkdir(parents=True, exist_ok=True)

    state_dir = (
        Path(args.state_dir).expanduser()
        if args.state_dir
        else config_dir / "multi_state"
    )
    state_dir.mkdir(parents=True, exist_ok=True)

    sa_key_path = Path(args.service_account_key).expanduser().resolve()
    if not sa_key_path.exists():
        fail(f"service account key file not found: {sa_key_path}")

    output_dir = Path(args.output_dir).expanduser().resolve()

    user_emails = _load_users(args)
    if not user_emails:
        fail("no users to process (empty --impersonate-users or empty file)")

    try:
        query = _build_search_query(args)
    except ValueError as e:
        fail(str(e))

    query_string = build_gmail_query(query)
    clock = SystemClock()

    multi_plan_id = build_multi_plan_id(
        account_emails=user_emails,
        query_string=query_string,
        output_format=args.format,
        timestamp=clock.now(),
    )

    accounts = _build_accounts(user_emails, config_dir)

    plan: MultiUserBackupPlan = {
        "multi_plan_id": multi_plan_id,
        "accounts": accounts,
        "query": query,
        "output_dir": str(output_dir),
        "output_format": args.format,
    }

    # DI 組み立て
    client_factory = GoogleGmailClientFactory(
        service_account_key_path=str(sa_key_path),
        scopes=list(DEFAULT_SCOPES),
    )
    writer = _make_writer(args.format, multi_plan_id)
    multi_state_repo = JsonMultiUserStateRepository()

    uc = MultiUserFetchBatchUseCase(
        client_factory=client_factory,
        writer=writer,
        multi_state_repo=multi_state_repo,
        clock=clock,
    )

    try:
        result = uc.execute(
            plan=plan,
            state_dir=str(state_dir),
            resume=args.resume,
            max_messages_per_user=args.max_messages_per_user,
        )
    except Exception as e:  # noqa: BLE001
        fail(f"multi-user backup failed: {e}", details={"multi_plan_id": multi_plan_id})

    print_success(
        {
            "multi_plan_id": result["multi_plan_id"],
            "user_count": len(user_emails),
            "query": query_string if query_string else "(all messages)",
            "output_dir": str(output_dir),
            "output_format": args.format,
            "per_user_success": result["per_user_success"],
            "per_user_failure": result["per_user_failure"],
            "per_user_deduped": result["per_user_deduped"],
            "total_unique_messages": result["total_unique_messages"],
            "total_dedup_skipped": result["total_dedup_skipped"],
            "total_messages_without_message_id": result[
                "total_messages_without_message_id"
            ],
            "output_files_count": len(result["output_files"]),
            "started_at": result["started_at"],
            "finished_at": result["finished_at"],
        }
    )


if __name__ == "__main__":
    main()

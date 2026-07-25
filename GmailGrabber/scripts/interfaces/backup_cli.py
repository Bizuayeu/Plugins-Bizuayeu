#!/usr/bin/env python3
"""
backup_cli
==========

Gmail バックアップ実行 CLI。

Usage:
    python -m interfaces.backup_cli \
        --email togami-log@meguru-construction.com \
        --client-secret /path/to/client_secret.json \
        --output-dir /path/to/BusinessWiki/data/2026-04 \
        --format eml \
        [--after 2026/04/01] [--before 2026/04/12] \
        [--from-addr user@example.com] [--subject "invoice"] \
        [--label INBOX] [--has-attachment] \
        [--raw-query "custom gmail query"] \
        [--max-messages 100] \
        [--no-resume] \
        [--state-dir /path/to/state]
"""

import argparse
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from application.auth.authenticate import AuthenticateUseCase
from application.fetch.fetch_batch import FetchBatchUseCase
from domain.constants import (
    DEFAULT_SCOPES,
    OUTPUT_FORMAT_EML,
    OUTPUT_FORMAT_MBOX,
    VALID_OUTPUT_FORMATS,
)
from domain.file_naming import build_plan_id
from domain.protocols import MessageWriterProtocol
from domain.query_builder import build_gmail_query
from domain.types.account import GmailAccount
from domain.types.backup import BackupPlan
from domain.types.query import DateRange, SearchQuery
from infrastructure.clock import SystemClock
from infrastructure.google_gmail.client import GoogleGmailClient
from infrastructure.google_gmail.oauth_provider import GoogleOAuthCredentialsProvider
from infrastructure.repositories.json_state_repository import JsonStateRepository
from infrastructure.writers.eml_writer import EmlFileWriter
from infrastructure.writers.mbox_writer import MboxFileWriter
from interfaces.cli_helpers import default_config_dir, fail, print_success


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="gmailgrabber-backup",
        description="Backup Gmail messages matching search criteria",
    )
    p.add_argument("--email", required=True)
    p.add_argument("--client-secret", required=True)
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
    p.add_argument("--max-messages", type=int, default=None)
    p.add_argument("--no-resume", dest="resume", action="store_false")
    p.add_argument("--config-dir", default=None)
    p.add_argument("--state-dir", default=None)
    p.add_argument("--account-label", default=None)
    return p


def _parse_date(value: Optional[str]) -> Optional[date]:
    if value is None:
        return None
    try:
        return datetime.strptime(value, "%Y/%m/%d").date()
    except ValueError as e:
        raise ValueError(f"invalid date format (expected YYYY/MM/DD): {value}") from e


def _build_search_query(args: argparse.Namespace) -> SearchQuery:
    after = _parse_date(args.after)
    before = _parse_date(args.before)
    date_range: Optional[DateRange] = None
    if after is not None or before is not None:
        date_range = {"start": after, "end": before}

    return {
        "from_addr": args.from_addr,
        "to_addr": args.to_addr,
        "subject": args.subject,
        "label": args.label,
        "date_range": date_range,
        "has_attachment": True if args.has_attachment else None,
        "raw_query": args.raw_query,
    }


def _build_account(
    email: str, client_secret: str, config_dir: Path, label: Optional[str]
) -> GmailAccount:
    label_value = label if label else email.split("@")[0]
    token_path = config_dir / f"token_{label_value}.json"
    return {
        "email": email,
        "label": label_value,
        "credentials_path": str(Path(client_secret).resolve()),
        "token_path": str(token_path.resolve()),
    }


def _make_writer(output_format: str, plan_id: str) -> MessageWriterProtocol:
    if output_format == OUTPUT_FORMAT_EML:
        return EmlFileWriter()
    if output_format == OUTPUT_FORMAT_MBOX:
        return MboxFileWriter(plan_id=plan_id)
    raise ValueError(f"unsupported format: {output_format}")


def main() -> None:
    args = _build_parser().parse_args()

    config_dir = Path(args.config_dir).expanduser() if args.config_dir else default_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)

    state_dir = Path(args.state_dir).expanduser() if args.state_dir else config_dir / "state"
    state_dir.mkdir(parents=True, exist_ok=True)

    output_dir = Path(args.output_dir).expanduser().resolve()

    try:
        query = _build_search_query(args)
    except ValueError as e:
        fail(str(e))

    account = _build_account(args.email, args.client_secret, config_dir, args.account_label)

    if not Path(account["credentials_path"]).exists():
        fail(f"client_secret file not found: {account['credentials_path']}")

    # 認証
    provider = GoogleOAuthCredentialsProvider()
    clock = SystemClock()
    auth_uc = AuthenticateUseCase(provider, clock)
    try:
        credentials = auth_uc.execute(account, scopes=DEFAULT_SCOPES)
    except Exception as e:  # noqa: BLE001
        fail(f"authentication failed: {e}")

    # Query → plan_id 生成
    query_string = build_gmail_query(query)
    plan_id = build_plan_id(
        account_email=account["email"],
        query_string=query_string,
        output_format=args.format,
        timestamp=clock.now(),
    )

    plan: BackupPlan = {
        "plan_id": plan_id,
        "account": account,
        "query": query,
        "output_dir": str(output_dir),
        "output_format": args.format,
    }

    # Gmail client + writer + state_repo で UseCase 組み立て
    gmail_client = GoogleGmailClient(credentials=credentials, user_id="me")
    writer = _make_writer(args.format, plan_id)
    state_repo = JsonStateRepository()

    uc = FetchBatchUseCase(gmail_client, writer, state_repo, clock)

    try:
        result = uc.execute(
            plan=plan,
            state_dir=str(state_dir),
            resume=args.resume,
            max_messages=args.max_messages,
        )
    except Exception as e:  # noqa: BLE001
        fail(f"backup failed: {e}", details={"plan_id": plan_id})

    print_success(
        {
            "plan_id": result["plan_id"],
            "account": account["email"],
            "query": query_string if query_string else "(all messages)",
            "output_dir": str(output_dir),
            "output_format": args.format,
            "success_count": result["success_count"],
            "failure_count": result["failure_count"],
            "output_files_count": len(result["output_files"]),
            "started_at": result["started_at"],
            "finished_at": result["finished_at"],
        }
    )


if __name__ == "__main__":
    main()

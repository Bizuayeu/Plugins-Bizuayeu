#!/usr/bin/env python3
"""
labels_cli
==========

Gmail ラベル一覧取得 CLI。

Usage:
    python -m interfaces.labels_cli \
        --email togami-log@meguru-construction.example.jp \
        --client-secret /path/to/client_secret.json
"""

import argparse
from pathlib import Path

from application.auth.authenticate import AuthenticateUseCase
from application.labels.list_labels import ListLabelsUseCase
from domain.constants import DEFAULT_SCOPES
from domain.types.account import GmailAccount
from infrastructure.clock import SystemClock
from infrastructure.google_gmail.client import GoogleGmailClient
from infrastructure.google_gmail.oauth_provider import GoogleOAuthCredentialsProvider
from interfaces.cli_helpers import default_config_dir, fail, print_success


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="gmailgrabber-labels",
        description="List all labels in a Gmail account",
    )
    p.add_argument("--email", required=True)
    p.add_argument("--client-secret", required=True)
    p.add_argument("--config-dir", default=None)
    p.add_argument("--account-label", default=None)
    return p


def _build_account(
    email: str, client_secret: str, config_dir: Path, label: str | None
) -> GmailAccount:
    label_value = label if label else email.split("@")[0]
    token_path = config_dir / f"token_{label_value}.json"
    return {
        "email": email,
        "label": label_value,
        "credentials_path": str(Path(client_secret).resolve()),
        "token_path": str(token_path.resolve()),
    }


def main() -> None:
    args = _build_parser().parse_args()
    config_dir = Path(args.config_dir).expanduser() if args.config_dir else default_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)

    account = _build_account(args.email, args.client_secret, config_dir, args.account_label)

    if not Path(account["credentials_path"]).exists():
        fail(f"client_secret file not found: {account['credentials_path']}")

    provider = GoogleOAuthCredentialsProvider()
    clock = SystemClock()
    auth_uc = AuthenticateUseCase(provider, clock)
    try:
        credentials = auth_uc.execute(account, scopes=DEFAULT_SCOPES)
    except Exception as e:  # noqa: BLE001
        fail(f"authentication failed: {e}")

    client = GoogleGmailClient(credentials=credentials, user_id="me")
    uc = ListLabelsUseCase(client)
    try:
        labels = uc.execute()
    except Exception as e:  # noqa: BLE001
        fail(f"failed to list labels: {e}")

    print_success(
        {
            "email": account["email"],
            "label_count": len(labels),
            "labels": labels,
        }
    )


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
auth_cli
========

OAuth 2.0 認証 CLI。

Usage:
    python -m interfaces.auth_cli \
        --email togami-log@meguru-construction.example.jp \
        --client-secret /path/to/client_secret.json \
        [--config-dir /path/to/config_dir]
"""

import argparse
from pathlib import Path
from typing import Optional

from application.auth.authenticate import AuthenticateUseCase
from domain.constants import DEFAULT_SCOPES
from domain.types.account import GmailAccount
from infrastructure.clock import SystemClock
from infrastructure.google_gmail.oauth_provider import GoogleOAuthCredentialsProvider
from interfaces.cli_helpers import default_config_dir, fail, print_success


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="gmailgrabber-auth",
        description="Authenticate a Gmail account via OAuth 2.0",
    )
    p.add_argument("--email", required=True, help="Gmail address to authenticate")
    p.add_argument(
        "--client-secret",
        required=True,
        help="Path to OAuth client_secret.json downloaded from Google Cloud Console",
    )
    p.add_argument(
        "--config-dir",
        default=None,
        help="Config dir for token storage (default: platform-specific)",
    )
    p.add_argument(
        "--label",
        default=None,
        help="Account label for filename/logs (default: local-part of email)",
    )
    return p


def _make_account(
    email: str,
    client_secret: str,
    config_dir: Path,
    label: Optional[str],
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

    account = _make_account(args.email, args.client_secret, config_dir, args.label)

    if not Path(account["credentials_path"]).exists():
        fail(
            f"client_secret file not found: {account['credentials_path']}",
            details={"email": args.email},
        )

    provider = GoogleOAuthCredentialsProvider()
    clock = SystemClock()
    uc = AuthenticateUseCase(provider, clock)

    try:
        credentials = uc.execute(account, scopes=DEFAULT_SCOPES)
    except Exception as e:  # noqa: BLE001
        fail(f"authentication failed: {e}", details={"email": args.email})

    print_success(
        {
            "email": account["email"],
            "label": account["label"],
            "token_path": account["token_path"],
            "scopes": credentials["scopes"],
            "expires_at": credentials.get("expires_at"),
        }
    )


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Account Domain Types
====================

Gmail アカウント情報とOAuth credentials のパス指定。

設計意図:
- GmailAccount は「どのGmailアカウントに、どのcredentialsで認証するか」の対
- credentials_path と token_path はファイルパス文字列（Path解決はinfrastructure層）
- 複数アカウント対応: アカウントごとに独立したtoken保存

Usage:
    from domain.types.account import GmailAccount

    acc: GmailAccount = {
        "email": "togami-log@meguru-construction.com",
        "label": "togami-log",
        "credentials_path": "/path/to/client_secret.json",
        "token_path": "/path/to/token_togami-log.json",
    }
"""

from typing import TypedDict


class GmailAccount(TypedDict):
    """
    Gmail アカウント設定

    Attributes:
        email: Gmailアドレス（正規化されたRFC5322形式を期待）
        label: 表示用の短縮名（ファイル名・ログ用）
        credentials_path: OAuth 2.0 client_secret.json ファイルパス
        token_path: 認証済みtoken保存先パス（初回認証時に生成）
    """

    email: str
    label: str
    credentials_path: str
    token_path: str


__all__ = ["GmailAccount"]

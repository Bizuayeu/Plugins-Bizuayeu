#!/usr/bin/env python3
"""
Domain Constants
================

Gmail API スコープ、デフォルト値、定数定義。
"""

from typing import Final

# Gmail API OAuth 2.0 スコープ
# https://developers.google.com/gmail/api/auth/scopes
GMAIL_READONLY_SCOPE: Final[str] = "https://www.googleapis.com/auth/gmail.readonly"
GMAIL_MODIFY_SCOPE: Final[str] = "https://www.googleapis.com/auth/gmail.modify"

# デフォルトスコープ: 読み取り専用
DEFAULT_SCOPES: Final[list[str]] = [GMAIL_READONLY_SCOPE]

# Gmail API エンドポイント
GMAIL_API_SERVICE_NAME: Final[str] = "gmail"
GMAIL_API_VERSION: Final[str] = "v1"

# Gmail API ページング
DEFAULT_PAGE_SIZE: Final[int] = 100
MAX_PAGE_SIZE: Final[int] = 500

# 出力形式
OUTPUT_FORMAT_EML: Final[str] = "eml"
OUTPUT_FORMAT_MBOX: Final[str] = "mbox"
VALID_OUTPUT_FORMATS: Final[list[str]] = [OUTPUT_FORMAT_EML, OUTPUT_FORMAT_MBOX]

# リトライ設定
DEFAULT_MAX_RETRIES: Final[int] = 3
DEFAULT_RETRY_BACKOFF_SECONDS: Final[float] = 2.0

# 状態ファイル
STATE_FILE_NAME: Final[str] = "backup_state.json"

# Gmail検索クエリ日付フォーマット (Gmail仕様: YYYY/MM/DD)
GMAIL_QUERY_DATE_FORMAT: Final[str] = "%Y/%m/%d"

__all__ = [
    "DEFAULT_MAX_RETRIES",
    "DEFAULT_PAGE_SIZE",
    "DEFAULT_RETRY_BACKOFF_SECONDS",
    "DEFAULT_SCOPES",
    "GMAIL_API_SERVICE_NAME",
    "GMAIL_API_VERSION",
    "GMAIL_MODIFY_SCOPE",
    "GMAIL_QUERY_DATE_FORMAT",
    "GMAIL_READONLY_SCOPE",
    "MAX_PAGE_SIZE",
    "OUTPUT_FORMAT_EML",
    "OUTPUT_FORMAT_MBOX",
    "STATE_FILE_NAME",
    "VALID_OUTPUT_FORMATS",
]

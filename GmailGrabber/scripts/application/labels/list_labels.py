#!/usr/bin/env python3
"""
ListLabelsUseCase
=================

Gmail アカウントの全ラベル一覧を取得するユースケース。
"""

from domain.protocols import GmailClientProtocol


class ListLabelsUseCase:
    """Gmail ラベル一覧取得ユースケース"""

    def __init__(self, gmail_client: GmailClientProtocol) -> None:
        self._client = gmail_client

    def execute(self) -> list[dict]:
        """
        全ラベル一覧を返す。

        Returns:
            dict のリスト (id, name, type キーを含む)
        """
        return self._client.list_labels()


__all__ = ["ListLabelsUseCase"]

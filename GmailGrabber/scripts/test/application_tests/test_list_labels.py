#!/usr/bin/env python3
"""
application/labels/list_labels.py テスト
========================================
"""

import pytest

from application.labels.list_labels import ListLabelsUseCase
from test.test_helpers import FakeGmailClient


class TestListLabels:
    @pytest.mark.unit
    def test_returns_empty_list_when_no_labels(self) -> None:
        client = FakeGmailClient(labels=[])
        uc = ListLabelsUseCase(client)
        assert uc.execute() == []

    @pytest.mark.unit
    def test_returns_all_labels(self) -> None:
        labels = [
            {"id": "INBOX", "name": "Inbox", "type": "system"},
            {"id": "Label_1", "name": "Work", "type": "user"},
        ]
        client = FakeGmailClient(labels=labels)
        uc = ListLabelsUseCase(client)
        result = uc.execute()
        assert len(result) == 2
        assert result[0]["name"] == "Inbox"
        assert result[1]["name"] == "Work"

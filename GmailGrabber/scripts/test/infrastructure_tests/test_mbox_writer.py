#!/usr/bin/env python3
"""
infrastructure/writers/mbox_writer.py テスト
============================================
"""

import mailbox
from datetime import datetime
from pathlib import Path

import pytest

from infrastructure.writers.mbox_writer import MboxFileWriter
from test.test_helpers import make_gmail_message


class TestMboxFileWriter:
    @pytest.mark.integration
    def test_write_single_message(self, tmp_path: Path) -> None:
        writer = MboxFileWriter(plan_id="plan_test_001")
        msg = make_gmail_message(
            "id1",
            raw_mime=b"From: a@b.com\r\nSubject: test\r\n\r\nbody",
        )

        path = writer.write(msg, str(tmp_path))
        writer.finalize(str(tmp_path))

        assert Path(path).exists()
        assert Path(path).name == "plan_test_001.mbox"

    @pytest.mark.integration
    def test_write_multiple_messages_same_file(self, tmp_path: Path) -> None:
        writer = MboxFileWriter(plan_id="plan_test_002")
        msgs = [
            make_gmail_message(
                f"id{i}",
                raw_mime=f"From: test{i}@example.com\r\n\r\nbody{i}".encode(),
            )
            for i in range(5)
        ]

        paths = [writer.write(m, str(tmp_path)) for m in msgs]
        finalized = writer.finalize(str(tmp_path))

        # 全て同じ mbox ファイル
        assert len(set(paths)) == 1
        assert len(finalized) == 1

    @pytest.mark.integration
    def test_mbox_can_be_read_back_with_mailbox_module(self, tmp_path: Path) -> None:
        """書き出した mbox が mailbox.mbox で再読み込みできる"""
        writer = MboxFileWriter(plan_id="plan_roundtrip")
        msgs = [
            make_gmail_message(
                f"id{i}",
                raw_mime=f"From: sender{i}@example.com\r\nSubject: msg{i}\r\n\r\nbody{i}".encode(),
            )
            for i in range(3)
        ]

        for m in msgs:
            writer.write(m, str(tmp_path))
        finalized = writer.finalize(str(tmp_path))

        # 読み直し
        mbox = mailbox.mbox(finalized[0])
        messages = list(mbox)
        assert len(messages) == 3
        mbox.close()

    @pytest.mark.integration
    def test_finalize_without_write_returns_empty(self, tmp_path: Path) -> None:
        writer = MboxFileWriter(plan_id="plan_empty")
        # write() を呼ばずに finalize()
        result = writer.finalize(str(tmp_path))
        assert result == []

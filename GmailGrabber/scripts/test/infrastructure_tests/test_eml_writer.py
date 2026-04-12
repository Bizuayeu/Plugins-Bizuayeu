#!/usr/bin/env python3
"""
infrastructure/writers/eml_writer.py テスト
===========================================
"""

from datetime import datetime
from pathlib import Path

import pytest

from infrastructure.writers.eml_writer import EmlFileWriter
from test.test_helpers import make_gmail_message


class TestEmlFileWriter:
    @pytest.mark.integration
    def test_write_single_eml(self, tmp_path: Path) -> None:
        writer = EmlFileWriter()
        msg = make_gmail_message(
            gmail_id="abc123",
            internal_date=datetime(2026, 4, 5, 14, 30, 12),
            raw_mime=b"From: test@example.com\r\nSubject: hello\r\n\r\nbody text",
        )

        result_path = writer.write(msg, str(tmp_path))

        assert Path(result_path).exists()
        assert Path(result_path).name == "20260405_143012_abc123.eml"
        assert Path(result_path).read_bytes() == msg["raw_mime"]

    @pytest.mark.integration
    def test_creates_nested_output_dir(self, tmp_path: Path) -> None:
        writer = EmlFileWriter()
        nested = tmp_path / "2026-04" / "nested"
        msg = make_gmail_message("x")

        writer.write(msg, str(nested))

        assert nested.exists()
        assert nested.is_dir()

    @pytest.mark.integration
    def test_write_multiple_eml_files(self, tmp_path: Path) -> None:
        writer = EmlFileWriter()
        msgs = [
            make_gmail_message(
                f"id{i}",
                internal_date=datetime(2026, 4, i + 1, 10, 0, 0),
            )
            for i in range(3)
        ]

        paths = [writer.write(m, str(tmp_path)) for m in msgs]

        for p in paths:
            assert Path(p).exists()
        assert len(list(tmp_path.glob("*.eml"))) == 3

    @pytest.mark.integration
    def test_finalize_returns_empty_list(self, tmp_path: Path) -> None:
        writer = EmlFileWriter()
        assert writer.finalize(str(tmp_path)) == []

    @pytest.mark.integration
    def test_raw_mime_preserved_byte_exact(self, tmp_path: Path) -> None:
        """Gmail API のバイナリ添付も壊さず保存されるか"""
        writer = EmlFileWriter()
        raw = b"\x00\x01\x02\x03binary\xff\xfe\xfd"
        msg = make_gmail_message("bin", raw_mime=raw)

        path = writer.write(msg, str(tmp_path))

        assert Path(path).read_bytes() == raw

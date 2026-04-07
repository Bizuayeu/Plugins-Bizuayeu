#!/usr/bin/env python3
"""
infrastructure/email_parser/format_detector.py テスト
======================================================

EmailFormat 検出ロジックのテスト。

検出戦略:
- 拡張子優先（.eml → eml、.mbox → mbox）
- 拡張子曖昧時はファイル先頭シグネチャ
- mbox: "From " で始まる行（mbox separator）
- eml: ヘッダ行（"<Field>: " 形式）
"""

import pytest

from infrastructure.email_parser.format_detector import (
    EmailFormat,
    detect_email_format,
)


class TestDetectByExtension:
    """拡張子ベース判定"""

    @pytest.mark.integration
    def test_eml_extension(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        f = tmp_path / "sample.eml"
        f.write_text("From: a@b\nSubject: x\n\nbody")
        assert detect_email_format(f) == EmailFormat.EML

    @pytest.mark.integration
    def test_mbox_extension(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        f = tmp_path / "sample.mbox"
        f.write_text("From a@b Mon Jan  1 00:00:00 2026\nSubject: x\n\nbody\n")
        assert detect_email_format(f) == EmailFormat.MBOX

    @pytest.mark.integration
    def test_eml_extension_uppercase(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        """拡張子の大文字小文字を区別しない"""
        f = tmp_path / "sample.EML"
        f.write_text("Subject: x\n\n")
        assert detect_email_format(f) == EmailFormat.EML


class TestDetectBySignature:
    """シグネチャベース判定（拡張子なしや .txt 等）"""

    @pytest.mark.integration
    def test_mbox_signature(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        f = tmp_path / "sample.txt"
        f.write_text("From a@b Mon Jan  1 00:00:00 2026\nSubject: x\n")
        assert detect_email_format(f) == EmailFormat.MBOX

    @pytest.mark.integration
    def test_eml_signature_with_header(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        f = tmp_path / "sample.txt"
        f.write_text("From: a@b\nTo: c@d\nSubject: x\n\nbody")
        assert detect_email_format(f) == EmailFormat.EML

    @pytest.mark.integration
    def test_unknown_format(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        f = tmp_path / "sample.txt"
        f.write_text("hello world")
        with pytest.raises(ValueError, match="cannot detect"):
            detect_email_format(f)


class TestDetectErrors:
    @pytest.mark.integration
    def test_nonexistent_file(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        with pytest.raises(FileNotFoundError):
            detect_email_format(tmp_path / "nope.eml")

    @pytest.mark.integration
    def test_directory_raises(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        with pytest.raises(IsADirectoryError):
            detect_email_format(tmp_path)

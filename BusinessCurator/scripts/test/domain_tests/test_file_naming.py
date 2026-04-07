#!/usr/bin/env python3
"""
domain/file_naming.py テスト
============================

エントリID生成とファイル名サニタイズの単体テスト。

設計意図:
- make_entry_id: datetime + メッセージID hash → "email_YYYYMMDD_HHMMSS_xxxxxxxx"
- parse_entry_id: ID 文字列 → (datetime, hash) の逆操作
- sanitize_filename: OS 互換のファイル名生成（Windows 禁止文字対応）
- 冪等性: 同じ入力なら同じ出力
"""

from datetime import datetime

import pytest

from domain.constants import ENTRY_ID_HASH_LENGTH, ENTRY_ID_PREFIX
from domain.file_naming import (
    is_valid_entry_id,
    make_entry_id,
    parse_entry_id,
    sanitize_filename,
)

# =============================================================================
# make_entry_id
# =============================================================================


class TestMakeEntryId:
    """make_entry_id 関数のテスト"""

    @pytest.mark.unit
    def test_basic_format(self) -> None:
        """基本フォーマット: email_YYYYMMDD_HHMMSS_xxxxxxxx"""
        dt = datetime(2026, 4, 7, 14, 30, 22)
        eid = make_entry_id(dt, "<abc@example.com>")
        # email_20260407_143022_<8文字>
        assert eid.startswith("email_20260407_143022_")
        suffix = eid.rsplit("_", 1)[-1]
        assert len(suffix) == ENTRY_ID_HASH_LENGTH

    @pytest.mark.unit
    def test_starts_with_prefix(self) -> None:
        """プレフィックスは ENTRY_ID_PREFIX"""
        dt = datetime(2026, 1, 1, 0, 0, 0)
        eid = make_entry_id(dt, "msg")
        assert eid.startswith(ENTRY_ID_PREFIX)

    @pytest.mark.unit
    def test_idempotent(self) -> None:
        """同一入力に対し冪等"""
        dt = datetime(2026, 4, 7, 14, 30, 22)
        eid1 = make_entry_id(dt, "<abc@example.com>")
        eid2 = make_entry_id(dt, "<abc@example.com>")
        assert eid1 == eid2

    @pytest.mark.unit
    def test_different_message_id_yields_different_hash(self) -> None:
        """異なる message_id は異なる hash を生む"""
        dt = datetime(2026, 4, 7, 14, 30, 22)
        eid1 = make_entry_id(dt, "<abc@example.com>")
        eid2 = make_entry_id(dt, "<xyz@example.com>")
        assert eid1 != eid2

    @pytest.mark.unit
    def test_zero_padding(self) -> None:
        """日時の0埋め（1月→01、5時→05）"""
        dt = datetime(2026, 1, 5, 9, 7, 3)
        eid = make_entry_id(dt, "msg")
        assert "20260105_090703" in eid

    @pytest.mark.unit
    def test_empty_message_id_still_works(self) -> None:
        """空 message_id でも生成可能（hash は空文字列の hash）"""
        dt = datetime(2026, 4, 7, 14, 30, 22)
        eid = make_entry_id(dt, "")
        # フォーマットは保たれる
        assert eid.startswith("email_20260407_143022_")
        assert len(eid.rsplit("_", 1)[-1]) == ENTRY_ID_HASH_LENGTH


# =============================================================================
# parse_entry_id
# =============================================================================


class TestParseEntryId:
    """parse_entry_id 関数のテスト"""

    @pytest.mark.unit
    def test_round_trip(self) -> None:
        """make → parse のラウンドトリップで datetime が一致"""
        dt = datetime(2026, 4, 7, 14, 30, 22)
        eid = make_entry_id(dt, "<abc@example.com>")
        parsed_dt, _ = parse_entry_id(eid)
        assert parsed_dt == dt

    @pytest.mark.unit
    def test_returns_hash_suffix(self) -> None:
        """parse は (datetime, hash) のタプルを返す"""
        dt = datetime(2026, 4, 7, 14, 30, 22)
        eid = make_entry_id(dt, "<abc@example.com>")
        _, hash_suffix = parse_entry_id(eid)
        assert len(hash_suffix) == ENTRY_ID_HASH_LENGTH

    @pytest.mark.unit
    def test_invalid_format_raises(self) -> None:
        """不正フォーマットで ValueError"""
        with pytest.raises(ValueError):
            parse_entry_id("not_an_entry_id")

    @pytest.mark.unit
    def test_missing_prefix_raises(self) -> None:
        """プレフィックス欠如で ValueError"""
        with pytest.raises(ValueError):
            parse_entry_id("20260407_143022_abc12345")

    @pytest.mark.unit
    def test_invalid_date_raises(self) -> None:
        """日付パース失敗で ValueError"""
        with pytest.raises(ValueError):
            parse_entry_id("email_99999999_999999_abc12345")


# =============================================================================
# is_valid_entry_id
# =============================================================================


class TestIsValidEntryId:
    """is_valid_entry_id 関数のテスト"""

    @pytest.mark.unit
    def test_valid_id_returns_true(self) -> None:
        """有効な ID で True"""
        dt = datetime(2026, 4, 7, 14, 30, 22)
        eid = make_entry_id(dt, "msg")
        assert is_valid_entry_id(eid) is True

    @pytest.mark.unit
    def test_invalid_id_returns_false(self) -> None:
        """無効な ID で False"""
        assert is_valid_entry_id("not_an_id") is False
        assert is_valid_entry_id("") is False
        assert is_valid_entry_id("email_99999999_999999_abcdefgh") is False


# =============================================================================
# sanitize_filename
# =============================================================================


class TestSanitizeFilename:
    """sanitize_filename 関数のテスト"""

    @pytest.mark.unit
    def test_safe_name_unchanged(self) -> None:
        """安全なファイル名はそのまま"""
        assert sanitize_filename("hello.txt") == "hello.txt"
        assert sanitize_filename("ProjectName_2026.md") == "ProjectName_2026.md"

    @pytest.mark.unit
    def test_japanese_preserved(self) -> None:
        """日本語は保持される（ファイル名として有効）"""
        assert sanitize_filename("案件名.md") == "案件名.md"

    @pytest.mark.unit
    def test_windows_forbidden_chars_replaced(self) -> None:
        """Windows 禁止文字が置換される"""
        # < > : " / \ | ? *
        result = sanitize_filename("a<b>c:d\"e/f\\g|h?i*j.txt")
        for forbidden in '<>:"/\\|?*':
            assert forbidden not in result

    @pytest.mark.unit
    def test_slash_replaced(self) -> None:
        """スラッシュ置換（パス区切りとの混同回避）"""
        result = sanitize_filename("a/b.txt")
        assert "/" not in result

    @pytest.mark.unit
    def test_leading_trailing_whitespace_stripped(self) -> None:
        """前後の空白を除去"""
        assert sanitize_filename("  hello.txt  ") == "hello.txt"

    @pytest.mark.unit
    def test_empty_input_raises(self) -> None:
        """空文字列で ValueError"""
        with pytest.raises(ValueError):
            sanitize_filename("")

    @pytest.mark.unit
    def test_whitespace_only_raises(self) -> None:
        """空白のみで ValueError"""
        with pytest.raises(ValueError):
            sanitize_filename("   ")

    @pytest.mark.unit
    def test_dots_only_raises(self) -> None:
        """.のみ/..のみで ValueError"""
        with pytest.raises(ValueError):
            sanitize_filename(".")
        with pytest.raises(ValueError):
            sanitize_filename("..")

    @pytest.mark.unit
    def test_max_length_truncation(self) -> None:
        """255 文字を超える場合は切り詰め（拡張子は保持）"""
        long_name = "a" * 300 + ".md"
        result = sanitize_filename(long_name)
        assert len(result) <= 255
        assert result.endswith(".md")

    @pytest.mark.unit
    def test_max_length_truncation_no_extension(self) -> None:
        """拡張子がないロングファイル名も切り詰められる"""
        long_name = "a" * 300
        result = sanitize_filename(long_name)
        assert len(result) == 255
        assert result == "a" * 255

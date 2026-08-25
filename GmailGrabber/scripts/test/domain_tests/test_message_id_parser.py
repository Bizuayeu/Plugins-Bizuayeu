#!/usr/bin/env python3
"""
domain/message_id_parser.py テスト
==================================
"""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from domain.message_id_parser import extract_message_id, normalize_message_id

# =============================================================================
# extract_message_id
# =============================================================================


class TestExtractMessageId:
    @pytest.mark.unit
    def test_extracts_standard_header(self) -> None:
        raw = b"Message-ID: <abc@example.com>\r\nFrom: a@b\r\n\r\nbody"
        assert extract_message_id(raw) == "<abc@example.com>"

    @pytest.mark.unit
    def test_extracts_lowercase_header(self) -> None:
        raw = b"message-id: <x@y.com>\r\n\r\nbody"
        assert extract_message_id(raw) == "<x@y.com>"

    @pytest.mark.unit
    def test_handles_mixed_case(self) -> None:
        raw = b"Message-Id: <y@z.com>\r\n\r\nbody"
        assert extract_message_id(raw) == "<y@z.com>"

    @pytest.mark.unit
    def test_missing_returns_none(self) -> None:
        raw = b"From: a@b.com\r\nSubject: hi\r\n\r\nbody"
        assert extract_message_id(raw) is None

    @pytest.mark.unit
    def test_empty_bytes_returns_none(self) -> None:
        assert extract_message_id(b"") is None

    @pytest.mark.unit
    def test_malformed_mime_returns_none(self) -> None:
        """完全にぶっ壊れたバイト列は None"""
        raw = b"\xff\xfe\xfd not a mime \x00\x01"
        # Python email パーサは堅牢なのでパースは通るが Message-ID は無い
        result = extract_message_id(raw)
        assert result is None

    @pytest.mark.unit
    def test_multiline_header_unfolded(self) -> None:
        """複数行ヘッダ (folded) は Python email パーサが unfold する"""
        raw = b"Message-ID:\r\n <abc@ex.com>\r\n\r\nbody"
        result = extract_message_id(raw)
        assert result == "<abc@ex.com>"

    @pytest.mark.unit
    def test_strips_surrounding_whitespace(self) -> None:
        raw = b"Message-ID:   <x@y.com>   \r\n\r\nbody"
        assert extract_message_id(raw) == "<x@y.com>"

    @pytest.mark.unit
    def test_empty_message_id_value_returns_none(self) -> None:
        raw = b"Message-ID: \r\n\r\nbody"
        assert extract_message_id(raw) is None

    @pytest.mark.unit
    def test_real_gmail_style_headers(self) -> None:
        raw = (
            b"Delivered-To: user@meguru-construction.example.jp\r\n"
            b"Received: by 2002:...\r\n"
            b"Message-ID: <CABcDeFGHi123+test@mail.gmail.com>\r\n"
            b"Date: Fri, 11 Apr 2026 10:00:00 +0900\r\n"
            b"From: sender@example.com\r\n"
            b"Subject: Test\r\n"
            b"\r\n"
            b"body text"
        )
        assert extract_message_id(raw) == "<CABcDeFGHi123+test@mail.gmail.com>"


# =============================================================================
# normalize_message_id
# =============================================================================


class TestNormalizeMessageId:
    @pytest.mark.unit
    def test_already_lowercase_unchanged(self) -> None:
        assert normalize_message_id("<abc@example.com>") == "<abc@example.com>"

    @pytest.mark.unit
    def test_domain_part_lowercased(self) -> None:
        assert normalize_message_id("<ABC@Example.COM>") == "<ABC@example.com>"

    @pytest.mark.unit
    def test_local_part_preserved(self) -> None:
        """ローカル部は case-sensitive 維持 (RFC 5321)"""
        assert normalize_message_id("<UserName@domain.com>") == "<UserName@domain.com>"

    @pytest.mark.unit
    def test_strip_brackets_option(self) -> None:
        result = normalize_message_id("<x@y.com>", strip_brackets=True)
        assert result == "x@y.com"

    @pytest.mark.unit
    def test_strip_brackets_with_case_normalization(self) -> None:
        result = normalize_message_id("<X@Y.COM>", strip_brackets=True)
        assert result == "X@y.com"

    @pytest.mark.unit
    def test_leading_trailing_whitespace_removed(self) -> None:
        assert normalize_message_id("  <x@y.com>  ") == "<x@y.com>"

    @pytest.mark.unit
    def test_no_at_sign_passes_through(self) -> None:
        """@ が無い変なIDも壊れず返る"""
        assert normalize_message_id("<weird>") == "<weird>"

    @pytest.mark.unit
    def test_case_insensitive_comparison(self) -> None:
        """2つの異なる大文字小文字表現が正規化後は同一"""
        a = normalize_message_id("<ABC@Example.COM>")
        b = normalize_message_id("<ABC@example.com>")
        assert a == b


# =============================================================================
# Property-based
# =============================================================================


@st.composite
def _simple_message_id(draw: st.DrawFn) -> str:
    local = draw(
        st.text(
            alphabet="abcdefghijklmnopqrstuvwxyz0123456789+", min_size=1, max_size=20
        )
    )
    domain = draw(
        st.text(alphabet="abcdefghijklmnopqrstuvwxyz.", min_size=3, max_size=20)
    )
    # ドメインは少なくとも 1 つの . を含むようにするわけでもないがテスト側で許容
    return f"<{local}@{domain}>"


class TestProperties:
    @pytest.mark.property
    @given(mid=_simple_message_id())
    def test_normalize_is_idempotent(self, mid: str) -> None:
        once = normalize_message_id(mid)
        twice = normalize_message_id(once)
        assert once == twice

    @pytest.mark.property
    @given(mid=_simple_message_id())
    def test_extract_roundtrip(self, mid: str) -> None:
        """生の Message-ID を MIME に埋めて抽出すると同じ値"""
        raw = f"Message-ID: {mid}\r\nFrom: a@b\r\n\r\nbody".encode("ascii")
        extracted = extract_message_id(raw)
        assert extracted == mid

    @pytest.mark.property
    @given(mid=_simple_message_id())
    def test_strip_brackets_roundtrip(self, mid: str) -> None:
        with_brackets = normalize_message_id(mid, strip_brackets=False)
        without_brackets = normalize_message_id(mid, strip_brackets=True)
        assert with_brackets == f"<{without_brackets}>"

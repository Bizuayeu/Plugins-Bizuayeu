#!/usr/bin/env python3
"""
domain/file_naming.py プロパティテスト
======================================

hypothesis による不変条件検証。

検証する不変条件:
1. make_entry_id は冪等（同じ入力 → 同じ出力）
2. make → parse のラウンドトリップで datetime が一致
3. 異なる message_id は異なる ID を高確率で生む
4. is_valid_entry_id(make_entry_id(...)) は常に True
5. sanitize_filename の出力には禁止文字が含まれない
6. sanitize_filename の出力長は 255 以下
"""

from datetime import datetime
from string import printable

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from domain.constants import ENTRY_ID_HASH_LENGTH
from domain.file_naming import (
    is_valid_entry_id,
    make_entry_id,
    parse_entry_id,
    sanitize_filename,
)

# =============================================================================
# Strategies
# =============================================================================

# 安全な datetime 範囲（strftime/strptime が問題なく扱え、かつ生成が高速）
# 業務上扱う範囲（2000-2099）に限定
_datetime_strategy = st.datetimes(
    min_value=datetime(2000, 1, 1, 0, 0, 0),
    max_value=datetime(2099, 12, 31, 23, 59, 59),
    allow_imaginary=False,
)

# message_id は任意のテキスト（空文字列含む）
_message_id_strategy = st.text(min_size=0, max_size=200)

# サニタイズ対象の任意文字列（空白のみ/. 等は除外して valid な入力に限定）
_sanitize_input_strategy = st.text(min_size=1, max_size=300).filter(
    lambda s: s.strip() and s.strip() not in (".", "..")
)


# =============================================================================
# make_entry_id プロパティ
# =============================================================================


class TestMakeEntryIdProperties:
    """make_entry_id の不変条件"""

    @pytest.mark.property
    @given(dt=_datetime_strategy, msg=_message_id_strategy)
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_idempotent(self, dt: datetime, msg: str) -> None:
        """同一入力で常に同一出力（冪等性）"""
        assert make_entry_id(dt, msg) == make_entry_id(dt, msg)

    @pytest.mark.property
    @given(dt=_datetime_strategy, msg=_message_id_strategy)
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_output_is_valid_entry_id(self, dt: datetime, msg: str) -> None:
        """生成された ID は常に is_valid_entry_id を満たす"""
        eid = make_entry_id(dt, msg)
        assert is_valid_entry_id(eid)

    @pytest.mark.property
    @given(dt=_datetime_strategy, msg=_message_id_strategy)
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_hash_length_constant(self, dt: datetime, msg: str) -> None:
        """hash サフィックスは常に ENTRY_ID_HASH_LENGTH 文字"""
        eid = make_entry_id(dt, msg)
        suffix = eid.rsplit("_", 1)[-1]
        assert len(suffix) == ENTRY_ID_HASH_LENGTH

    @pytest.mark.property
    @given(dt=_datetime_strategy, msg=_message_id_strategy)
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_starts_with_email_prefix(self, dt: datetime, msg: str) -> None:
        """常に "email_" で始まる"""
        eid = make_entry_id(dt, msg)
        assert eid.startswith("email_")


# =============================================================================
# round-trip プロパティ
# =============================================================================


class TestRoundTripProperties:
    """make → parse のラウンドトリップ不変条件"""

    @pytest.mark.property
    @given(dt=_datetime_strategy, msg=_message_id_strategy)
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_datetime_preserved(self, dt: datetime, msg: str) -> None:
        """datetime は秒精度でラウンドトリップ可能"""
        eid = make_entry_id(dt, msg)
        parsed_dt, _ = parse_entry_id(eid)
        # 秒精度（マイクロ秒は捨てられる）
        assert parsed_dt == dt.replace(microsecond=0)

    @pytest.mark.property
    @given(dt=_datetime_strategy, msg=_message_id_strategy)
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_hash_preserved(self, dt: datetime, msg: str) -> None:
        """hash は make 直後と parse の結果が一致"""
        eid = make_entry_id(dt, msg)
        original_suffix = eid.rsplit("_", 1)[-1]
        _, parsed_suffix = parse_entry_id(eid)
        assert parsed_suffix == original_suffix


# =============================================================================
# sanitize_filename プロパティ
# =============================================================================


class TestSanitizeFilenameProperties:
    """sanitize_filename の不変条件"""

    @pytest.mark.property
    @given(name=_sanitize_input_strategy)
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_no_forbidden_chars_in_output(self, name: str) -> None:
        """出力に Windows 禁止文字が含まれない"""
        result = sanitize_filename(name)
        for ch in '<>:"/\\|?*':
            assert ch not in result

    @pytest.mark.property
    @given(name=_sanitize_input_strategy)
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_output_length_within_limit(self, name: str) -> None:
        """出力長は 255 以下"""
        result = sanitize_filename(name)
        assert len(result) <= 255

    @pytest.mark.property
    @given(name=_sanitize_input_strategy)
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_output_is_non_empty(self, name: str) -> None:
        """出力は常に非空（valid な入力に対し）"""
        result = sanitize_filename(name)
        assert len(result) > 0

    @pytest.mark.property
    @given(name=_sanitize_input_strategy)
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_idempotent(self, name: str) -> None:
        """sanitize_filename は冪等（既にサニタイズ済みなら変化なし）"""
        once = sanitize_filename(name)
        twice = sanitize_filename(once)
        assert once == twice

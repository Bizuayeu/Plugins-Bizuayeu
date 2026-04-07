#!/usr/bin/env python3
"""
domain/validation.py テスト
===========================

TypedDict ランタイムバリデータのテスト。

設計意図:
- TypedDict は静的型のみ。実行時は dict そのもの → 検証関数を別途用意
- 外部入力（YAML、JSON、ユーザー入力）から RawEntry/AliasRecord 等を構築する際に使う
- 失敗時は ValidationError（BusinessCuratorError 派生）を投げる
"""

import pytest

from domain.exceptions import BusinessCuratorError
from domain.validation import (
    ValidationError,
    validate_alias_record,
    validate_raw_entry,
    validate_shard_kind,
)

# =============================================================================
# ValidationError
# =============================================================================


class TestValidationError:
    """ValidationError は BusinessCuratorError 派生"""

    @pytest.mark.unit
    def test_extends_business_curator_error(self) -> None:
        assert issubclass(ValidationError, BusinessCuratorError)


# =============================================================================
# validate_shard_kind
# =============================================================================


class TestValidateShardKind:
    """validate_shard_kind のテスト"""

    @pytest.mark.unit
    @pytest.mark.parametrize("kind", ["projects", "clients", "vendors", "knowledge"])
    def test_valid_kinds_pass(self, kind: str) -> None:
        """4種すべて通過"""
        validate_shard_kind(kind)  # raises なし

    @pytest.mark.unit
    def test_invalid_kind_raises(self) -> None:
        """未定義 kind で ValidationError"""
        with pytest.raises(ValidationError, match="invalid shard kind"):
            validate_shard_kind("unknown")

    @pytest.mark.unit
    def test_empty_string_raises(self) -> None:
        """空文字列で ValidationError"""
        with pytest.raises(ValidationError):
            validate_shard_kind("")

    @pytest.mark.unit
    def test_non_string_raises(self) -> None:
        """非文字列で ValidationError"""
        with pytest.raises(ValidationError):
            validate_shard_kind(123)  # type: ignore[arg-type]


# =============================================================================
# validate_raw_entry
# =============================================================================


class TestValidateRawEntry:
    """validate_raw_entry のテスト"""

    @pytest.fixture
    def valid_entry(self) -> dict:  # type: ignore[type-arg]
        return {
            "id": "email_20260407_143022_abc12345",
            "date": "2026-04-07",
            "time": "14:30:22",
            "source_type": "email",
            "from_addr": "ichikawa@meguru.co.jp",
            "to_addrs": ["oowanushi@meguru.co.jp"],
            "cc_addrs": [],
            "subject": "test",
            "thread_id": None,
            "attachments": [],
            "tags": [],
            "body": "hello",
        }

    @pytest.mark.unit
    def test_valid_entry_passes(self, valid_entry: dict) -> None:  # type: ignore[type-arg]
        validate_raw_entry(valid_entry)

    @pytest.mark.unit
    def test_missing_id_raises(self, valid_entry: dict) -> None:  # type: ignore[type-arg]
        del valid_entry["id"]
        with pytest.raises(ValidationError, match="id"):
            validate_raw_entry(valid_entry)

    @pytest.mark.unit
    def test_missing_required_field_raises(self, valid_entry: dict) -> None:  # type: ignore[type-arg]
        del valid_entry["subject"]
        with pytest.raises(ValidationError, match="subject"):
            validate_raw_entry(valid_entry)

    @pytest.mark.unit
    def test_invalid_id_format_raises(self, valid_entry: dict) -> None:  # type: ignore[type-arg]
        valid_entry["id"] = "not_a_valid_id"
        with pytest.raises(ValidationError, match="id"):
            validate_raw_entry(valid_entry)

    @pytest.mark.unit
    def test_to_addrs_must_be_list(self, valid_entry: dict) -> None:  # type: ignore[type-arg]
        valid_entry["to_addrs"] = "single@example.com"
        with pytest.raises(ValidationError, match="to_addrs"):
            validate_raw_entry(valid_entry)

    @pytest.mark.unit
    def test_thread_id_can_be_none(self, valid_entry: dict) -> None:  # type: ignore[type-arg]
        valid_entry["thread_id"] = None
        validate_raw_entry(valid_entry)

    @pytest.mark.unit
    def test_thread_id_can_be_string(self, valid_entry: dict) -> None:  # type: ignore[type-arg]
        valid_entry["thread_id"] = "thread_xyz"
        validate_raw_entry(valid_entry)

    @pytest.mark.unit
    def test_thread_id_int_raises(self, valid_entry: dict) -> None:  # type: ignore[type-arg]
        """thread_id が int だと ValidationError"""
        valid_entry["thread_id"] = 42
        with pytest.raises(ValidationError, match="thread_id"):
            validate_raw_entry(valid_entry)

    @pytest.mark.unit
    def test_to_addrs_with_non_string_element_raises(self, valid_entry: dict) -> None:  # type: ignore[type-arg]
        """to_addrs リストの要素が文字列でないと ValidationError"""
        valid_entry["to_addrs"] = ["a@b", 42]
        with pytest.raises(ValidationError, match="to_addrs"):
            validate_raw_entry(valid_entry)

    @pytest.mark.unit
    def test_non_dict_raises(self) -> None:
        with pytest.raises(ValidationError):
            validate_raw_entry("not a dict")  # type: ignore[arg-type]


# =============================================================================
# validate_alias_record
# =============================================================================


class TestValidateAliasRecord:
    """validate_alias_record のテスト"""

    @pytest.fixture
    def valid_record(self) -> dict:  # type: ignore[type-arg]
        return {
            "id": "projects/MaruMaruMansion",
            "canonical": "○○マンション新築工事",
            "aliases": ["○○MS", "現場番号2026-003"],
            "shard": "projects",
            "target_path": "shards/projects/MaruMaruMansion/_project.md",
            "archived": False,
        }

    @pytest.mark.unit
    def test_valid_record_passes(self, valid_record: dict) -> None:  # type: ignore[type-arg]
        validate_alias_record(valid_record)

    @pytest.mark.unit
    def test_id_format_must_be_kind_slash_slug(self, valid_record: dict) -> None:  # type: ignore[type-arg]
        valid_record["id"] = "no_slash"
        with pytest.raises(ValidationError, match="id"):
            validate_alias_record(valid_record)

    @pytest.mark.unit
    def test_id_kind_must_match_shard(self, valid_record: dict) -> None:  # type: ignore[type-arg]
        valid_record["id"] = "clients/MaruMaruMansion"
        valid_record["shard"] = "projects"
        with pytest.raises(ValidationError):
            validate_alias_record(valid_record)

    @pytest.mark.unit
    def test_invalid_shard_raises(self, valid_record: dict) -> None:  # type: ignore[type-arg]
        valid_record["shard"] = "invalid"
        with pytest.raises(ValidationError):
            validate_alias_record(valid_record)

    @pytest.mark.unit
    def test_aliases_must_be_list(self, valid_record: dict) -> None:  # type: ignore[type-arg]
        valid_record["aliases"] = "single"
        with pytest.raises(ValidationError, match="aliases"):
            validate_alias_record(valid_record)

    @pytest.mark.unit
    def test_archived_must_be_bool(self, valid_record: dict) -> None:  # type: ignore[type-arg]
        valid_record["archived"] = "false"
        with pytest.raises(ValidationError, match="archived"):
            validate_alias_record(valid_record)

    @pytest.mark.unit
    def test_id_with_empty_slug_raises(self, valid_record: dict) -> None:  # type: ignore[type-arg]
        """projects/ のように slug 部が空なら ValidationError"""
        valid_record["id"] = "projects/"
        with pytest.raises(ValidationError, match="empty kind or slug"):
            validate_alias_record(valid_record)

    @pytest.mark.unit
    def test_id_with_empty_kind_raises(self, valid_record: dict) -> None:  # type: ignore[type-arg]
        """/MaruMaruMansion のように kind 部が空なら ValidationError"""
        valid_record["id"] = "/MaruMaruMansion"
        with pytest.raises(ValidationError, match="empty kind or slug"):
            validate_alias_record(valid_record)

    @pytest.mark.unit
    def test_id_must_be_string(self, valid_record: dict) -> None:  # type: ignore[type-arg]
        """id が文字列でないと ValidationError"""
        valid_record["id"] = 12345
        with pytest.raises(ValidationError, match="id"):
            validate_alias_record(valid_record)

    @pytest.mark.unit
    def test_non_dict_input_raises(self) -> None:
        """非 dict で ValidationError"""
        with pytest.raises(ValidationError, match="alias record must be dict"):
            validate_alias_record("not a dict")  # type: ignore[arg-type]

    @pytest.mark.unit
    def test_missing_canonical_raises(self, valid_record: dict) -> None:  # type: ignore[type-arg]
        """canonical 欠落で ValidationError"""
        del valid_record["canonical"]
        with pytest.raises(ValidationError, match="canonical"):
            validate_alias_record(valid_record)


# =============================================================================
# 内部 helper の bool/int 区別
# =============================================================================


class TestRequireTypeBoolIntDistinction:
    """_require_type の bool/int 区別（archived のような True/False が誤って int 扱いされない）"""

    @pytest.mark.unit
    def test_bool_passed_to_int_field_raises(self) -> None:
        """int 期待のフィールドに bool を渡すと ValidationError

        Note: Python では bool は int のサブクラスだが、TypedDict では区別したい。
        validate_raw_entry が将来 int フィールドを持つときの境界条件として担保。
        """
        from domain.validation import _require_type

        with pytest.raises(ValidationError, match="must be int, got bool"):
            _require_type(True, int, "some_int_field")

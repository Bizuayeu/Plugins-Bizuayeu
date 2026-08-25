#!/usr/bin/env python3
"""
Runtime Validation
==================

TypedDict ランタイムバリデータ群。

設計意図:
- TypedDict は静的型のみ。実行時は dict そのもの → 検証関数が必要
- 外部入力（YAML/JSON/ユーザー入力）からドメイン型を構築する境界で使用
- 失敗時は ValidationError（BusinessCuratorError 派生）を投げる

Usage:
    from domain.validation import validate_raw_entry, ValidationError

    try:
        validate_raw_entry(yaml_data)
    except ValidationError as e:
        logger.error(f"Invalid entry: {e}")
"""

from typing import Any

from domain.constants import SHARD_KINDS
from domain.exceptions import BusinessCuratorError
from domain.file_naming import is_valid_entry_id
from domain.types.shard import ARCHIVE_STATUSES

__all__ = [
    "ValidationError",
    "validate_alias_record",
    "validate_raw_entry",
    "validate_shard_kind",
]


class ValidationError(BusinessCuratorError):
    """
    バリデーションエラー

    Examples:
        - 必須フィールド欠落
        - フィールド型不一致
        - 値制約違反（不正な ShardKind 等）
    """

    pass


# =============================================================================
# Helper
# =============================================================================


def _require_type(value: Any, expected: type, field: str) -> None:
    """型チェック（bool は int と区別する）"""
    if expected is int and isinstance(value, bool):
        raise ValidationError(f"field {field} must be int, got bool")
    if not isinstance(value, expected):
        raise ValidationError(
            f"field {field} must be {expected.__name__}, got {type(value).__name__}"
        )


def _require_list_of_str(value: Any, field: str) -> None:
    """list[str] チェック"""
    if not isinstance(value, list):
        raise ValidationError(f"field {field} must be list, got {type(value).__name__}")
    for i, item in enumerate(value):
        if not isinstance(item, str):
            raise ValidationError(
                f"field {field}[{i}] must be str, got {type(item).__name__}"
            )


# =============================================================================
# validate_shard_kind
# =============================================================================


def validate_shard_kind(value: Any) -> None:
    """
    ShardKind の妥当性を検証

    Args:
        value: 検証対象

    Raises:
        ValidationError: SHARD_KINDS のいずれでもない場合
    """
    if not isinstance(value, str):
        raise ValidationError(f"shard kind must be str, got {type(value).__name__}")
    if value not in SHARD_KINDS:
        raise ValidationError(
            f"invalid shard kind: {value!r} (expected one of {SHARD_KINDS})"
        )


# =============================================================================
# validate_raw_entry
# =============================================================================

_RAW_ENTRY_REQUIRED_FIELDS: list[str] = [
    "id",
    "date",
    "time",
    "source_type",
    "from_addr",
    "to_addrs",
    "cc_addrs",
    "subject",
    "thread_id",
    "attachments",
    "tags",
    "body",
]


def validate_raw_entry(data: Any) -> None:
    """
    RawEntry dict の妥当性を検証

    Args:
        data: 検証対象（dict 想定）

    Raises:
        ValidationError: フィールド欠落・型不一致・ID 形式不正
    """
    if not isinstance(data, dict):
        raise ValidationError(f"raw entry must be dict, got {type(data).__name__}")

    for field in _RAW_ENTRY_REQUIRED_FIELDS:
        if field not in data:
            raise ValidationError(f"missing required field: {field}")

    # id 形式検証
    if not is_valid_entry_id(data["id"]):
        raise ValidationError(f"invalid id format: {data['id']!r}")

    # 文字列フィールド
    for f in ["date", "time", "source_type", "from_addr", "subject", "body"]:
        _require_type(data[f], str, f)

    # list[str] フィールド
    for f in ["to_addrs", "cc_addrs", "attachments", "tags"]:
        _require_list_of_str(data[f], f)

    # thread_id は Optional[str]
    thread_id = data["thread_id"]
    if thread_id is not None and not isinstance(thread_id, str):
        raise ValidationError(
            f"thread_id must be str or None, got {type(thread_id).__name__}"
        )


# =============================================================================
# validate_alias_record
# =============================================================================


def validate_alias_record(data: Any) -> None:
    """
    AliasRecord dict の妥当性を検証

    Args:
        data: 検証対象（dict 想定）

    Raises:
        ValidationError: フィールド欠落・型不一致・ID/shard/archive_status 整合性違反
    """
    if not isinstance(data, dict):
        raise ValidationError(f"alias record must be dict, got {type(data).__name__}")

    for field in [
        "id",
        "canonical",
        "aliases",
        "shard",
        "target_path",
        "archive_status",
    ]:
        if field not in data:
            raise ValidationError(f"missing required field: {field}")

    # id は "kind/slug" 形式
    eid = data["id"]
    _require_type(eid, str, "id")
    if "/" not in eid:
        raise ValidationError(f"id must be in 'kind/slug' format, got {eid!r}")
    kind_part, slug_part = eid.split("/", 1)
    if not kind_part or not slug_part:
        raise ValidationError(f"id has empty kind or slug: {eid!r}")

    # shard 妥当性
    validate_shard_kind(data["shard"])

    # id の kind と shard の整合性
    if kind_part != data["shard"]:
        raise ValidationError(
            f"id kind {kind_part!r} does not match shard {data['shard']!r}"
        )

    # その他の文字列フィールド
    _require_type(data["canonical"], str, "canonical")
    _require_type(data["target_path"], str, "target_path")

    # aliases は list[str]
    _require_list_of_str(data["aliases"], "aliases")

    # archive_status は ARCHIVE_STATUSES のいずれか
    status = data["archive_status"]
    if not isinstance(status, str):
        raise ValidationError(
            f"archive_status must be str, got {type(status).__name__}"
        )
    if status not in ARCHIVE_STATUSES:
        raise ValidationError(
            f"invalid archive_status: {status!r} (expected one of {ARCHIVE_STATUSES})"
        )

    # target_path と archive_status の整合性
    target_path = data["target_path"]
    # status は単一値ゆえ 2 つのガードは排他。入れ子を畳んでも判定は変わらない。
    if status == "completed" and not target_path.startswith("archive/"):
        raise ValidationError(
            f"archive_status='completed' requires target_path under 'archive/', got {target_path!r}"
        )
    if status == "active" and not target_path.startswith("shards/"):
        raise ValidationError(
            f"archive_status='active' requires target_path under 'shards/', got {target_path!r}"
        )

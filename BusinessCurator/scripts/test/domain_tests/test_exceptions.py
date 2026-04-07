#!/usr/bin/env python3
"""
domain/exceptions.py テスト
===========================

例外階層のテスト。

設計意図:
- BusinessCuratorError: 全カスタム例外の基底
- 個別例外: IngestError, TriageError, ResolverError, ArchiveError, EntityNotFoundError
- DiagnosticContext で構造化エラー情報を保持
- EpisodicRAG exceptions.py のパターン踏襲
"""

import pytest

from domain.exceptions import (
    ArchiveError,
    BusinessCuratorError,
    DiagnosticContext,
    EntityNotFoundError,
    IngestError,
    ResolverError,
    TriageError,
)

# =============================================================================
# 例外階層
# =============================================================================


class TestExceptionHierarchy:
    """例外クラスの継承関係テスト"""

    @pytest.mark.unit
    def test_business_curator_error_extends_exception(self) -> None:
        """BusinessCuratorError は Exception を継承"""
        assert issubclass(BusinessCuratorError, Exception)

    @pytest.mark.unit
    def test_ingest_error_extends_business_curator_error(self) -> None:
        """IngestError は BusinessCuratorError を継承"""
        assert issubclass(IngestError, BusinessCuratorError)

    @pytest.mark.unit
    def test_triage_error_extends_business_curator_error(self) -> None:
        """TriageError は BusinessCuratorError を継承"""
        assert issubclass(TriageError, BusinessCuratorError)

    @pytest.mark.unit
    def test_resolver_error_extends_business_curator_error(self) -> None:
        """ResolverError は BusinessCuratorError を継承"""
        assert issubclass(ResolverError, BusinessCuratorError)

    @pytest.mark.unit
    def test_archive_error_extends_business_curator_error(self) -> None:
        """ArchiveError は BusinessCuratorError を継承"""
        assert issubclass(ArchiveError, BusinessCuratorError)

    @pytest.mark.unit
    def test_entity_not_found_error_extends_business_curator_error(self) -> None:
        """EntityNotFoundError は BusinessCuratorError を継承"""
        assert issubclass(EntityNotFoundError, BusinessCuratorError)


# =============================================================================
# BusinessCuratorError 基本動作
# =============================================================================


class TestBusinessCuratorError:
    """基底例外の動作テスト"""

    @pytest.mark.unit
    def test_can_raise_with_message(self) -> None:
        """メッセージ付きで raise 可能"""
        with pytest.raises(BusinessCuratorError, match="test error"):
            raise BusinessCuratorError("test error")

    @pytest.mark.unit
    def test_str_returns_message(self) -> None:
        """str() がメッセージを返す"""
        err = BusinessCuratorError("hello")
        assert "hello" in str(err)

    @pytest.mark.unit
    def test_can_raise_with_context(self) -> None:
        """DiagnosticContext 付きで raise 可能"""
        ctx = DiagnosticContext(operation="ingest", entry_id="email_001")
        with pytest.raises(BusinessCuratorError):
            raise BusinessCuratorError("failed", context=ctx)

    @pytest.mark.unit
    def test_str_includes_context_when_present(self) -> None:
        """context が設定されている場合 str() に含まれる"""
        ctx = DiagnosticContext(operation="ingest", entry_id="email_001")
        err = BusinessCuratorError("failed", context=ctx)
        s = str(err)
        assert "failed" in s
        assert "ingest" in s

    @pytest.mark.unit
    def test_context_is_optional(self) -> None:
        """context は省略可能"""
        err = BusinessCuratorError("simple")
        assert err.context is None


# =============================================================================
# DiagnosticContext
# =============================================================================


class TestDiagnosticContext:
    """DiagnosticContext のテスト"""

    @pytest.mark.unit
    def test_can_construct_empty(self) -> None:
        """全フィールド省略で構築可能"""
        ctx = DiagnosticContext()
        assert ctx.operation is None
        assert ctx.entry_id is None

    @pytest.mark.unit
    def test_to_dict_excludes_none_values(self) -> None:
        """to_dict() は None 値を除外"""
        ctx = DiagnosticContext(operation="triage", entry_id="email_001")
        d = ctx.to_dict()
        assert d == {"operation": "triage", "entry_id": "email_001"}

    @pytest.mark.unit
    def test_to_dict_empty_when_all_none(self) -> None:
        """全 None なら空辞書"""
        ctx = DiagnosticContext()
        assert ctx.to_dict() == {}

    @pytest.mark.unit
    def test_str_empty_when_all_none(self) -> None:
        """全 None なら str() は空文字列"""
        ctx = DiagnosticContext()
        assert str(ctx) == ""

    @pytest.mark.unit
    def test_str_formats_key_value_pairs(self) -> None:
        """str() は key=value 形式"""
        ctx = DiagnosticContext(operation="triage", file_count=3)
        s = str(ctx)
        assert "operation=triage" in s
        assert "file_count=3" in s

    @pytest.mark.unit
    def test_supports_additional_info(self) -> None:
        """additional_info で任意のキー追加可能"""
        ctx = DiagnosticContext(additional_info={"shard": "projects", "rule_count": 12})
        d = ctx.to_dict()
        assert d["shard"] == "projects"
        assert d["rule_count"] == 12

    @pytest.mark.unit
    def test_to_dict_includes_shard_kind(self) -> None:
        """shard_kind フィールドが to_dict に含まれる"""
        ctx = DiagnosticContext(shard_kind="projects")
        d = ctx.to_dict()
        assert d["shard_kind"] == "projects"

    @pytest.mark.unit
    def test_to_dict_includes_file_count(self) -> None:
        """file_count フィールドが to_dict に含まれる"""
        ctx = DiagnosticContext(file_count=10)
        d = ctx.to_dict()
        assert d["file_count"] == 10

    @pytest.mark.unit
    def test_to_dict_includes_file_path(self) -> None:
        """file_path フィールドが str 化されて to_dict に含まれる"""
        from pathlib import Path

        ctx = DiagnosticContext(file_path=Path("/tmp/test.eml"))
        d = ctx.to_dict()
        assert "test.eml" in d["file_path"]


class TestBusinessCuratorErrorEdgeCases:
    """基底例外のエッジケース"""

    @pytest.mark.unit
    def test_str_with_empty_context_skips_brackets(self) -> None:
        """空 DiagnosticContext を渡しても角括弧は付与されない"""
        ctx = DiagnosticContext()  # 全フィールド None
        err = BusinessCuratorError("simple", context=ctx)
        s = str(err)
        assert s == "simple"
        assert "[Context:" not in s


# =============================================================================
# 個別例外の利用
# =============================================================================


class TestSpecificExceptions:
    """個別例外の使用シナリオ"""

    @pytest.mark.unit
    def test_ingest_error_with_path_context(self) -> None:
        """IngestError をパスコンテキスト付きで使用"""
        from pathlib import Path

        ctx = DiagnosticContext(file_path=Path("/data/sample.eml"), operation="parse_email")
        with pytest.raises(IngestError, match="parse failed"):
            raise IngestError("parse failed", context=ctx)

    @pytest.mark.unit
    def test_resolver_error_for_duplicate_id(self) -> None:
        """重複 ID で ResolverError"""
        with pytest.raises(ResolverError, match="duplicate"):
            raise ResolverError("duplicate id: projects/Foo")

    @pytest.mark.unit
    def test_entity_not_found_error_with_id(self) -> None:
        """EntityNotFoundError を ID 付きで raise"""
        ctx = DiagnosticContext(additional_info={"entity_id": "projects/Unknown"})
        with pytest.raises(EntityNotFoundError):
            raise EntityNotFoundError("not found", context=ctx)

    @pytest.mark.unit
    def test_can_catch_all_via_base_class(self) -> None:
        """基底例外で全カスタム例外をキャッチできる"""
        try:
            raise TriageError("rule miss")
        except BusinessCuratorError as e:
            assert "rule miss" in str(e)
        else:
            pytest.fail("expected to be caught")
